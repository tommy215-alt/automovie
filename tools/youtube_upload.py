"""YouTube へ予約つきで上げる道具（Python の標準機能だけ。追加のインストールなし）。

  python tools/youtube_upload.py setup                     最初の 1 回。画面を順に開いて案内する（「YouTubeの設定を始める.bat」でも同じ）
  python tools/youtube_upload.py status                    予約ずみの本数と、次に空いている 18:00 の枠
  python tools/youtube_upload.py auth                      許可だけやり直す。ブラウザで許可する（ユーザー本人が実行する）
  python tools/youtube_upload.py check                     いまつながっているチャンネルを表示する
  python tools/youtube_upload.py upload videos/004 --at "2026-11-12 21:00" --dry-run   送る中身を見るだけ
  python tools/youtube_upload.py upload videos/004 --at "2026-11-12 21:00"            予約つきで上げる

安全のための決まり（この道具が自分で守る）
- 上げてよいチャンネルは publish/channel.json に書かれた 1 つだけ。違うチャンネルにつながっていたら止まる。
- チャンネル名に RE:VERSE／REVERSE を含むチャンネルには、何があっても上げない。
- 検査の結果（videos/NNN/qa.md）に未チェックの項目「- [ ]」が残っている回は上げない。
- 同じ回を 2 度上げない（publish/log/ に記録があれば止まる）。
- 認証のファイル（publish/client_secret.json、publish/token.json）は git に入れない。
"""
import argparse
import datetime
import http.server
import json
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.parent
PUB = ROOT / "publish"
SECRET, TOKEN, CHANNEL, LOG = PUB / "client_secret.json", PUB / "token.json", PUB / "channel.json", PUB / "log"
SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
JST = datetime.timezone(datetime.timedelta(hours=9))
CATEGORY = {"映画とアニメ": "1", "自動車と乗り物": "2", "音楽": "10", "ペットと動物": "15", "スポーツ": "17",
            "旅行とイベント": "19", "ゲーム": "20", "ブログ": "22", "コメディ": "23", "エンターテイメント": "24",
            "ニュースと政治": "25", "ハウツーとスタイル": "26", "教育": "27", "科学と技術": "28"}
FORBIDDEN = re.compile(r"RE\s*[:：]?\s*VERSE", re.I)


def die(msg):
    print("中止：" + msg)
    sys.exit(1)


def http(method, url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def client():
    if not SECRET.exists():
        die(f"{SECRET} がない。docs/UPLOAD_SETUP.md の手順で Google Cloud から取得して置く")
    j = json.loads(SECRET.read_text(encoding="utf-8"))
    return j.get("installed") or j.get("web") or die("client_secret.json の形式が違う（「デスクトップ アプリ」で作る）")


def auth():
    c = client()
    state = secrets.token_urlsafe(16)
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>許可を受け取りました。この画面は閉じてかまいません。</h2>".encode("utf-8"))

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code", "scope": SCOPES,
        "access_type": "offline", "prompt": "consent", "state": state})
    print("ブラウザが開きます。automovie 用の新しいチャンネルの Google アカウントで許可してください。\n開かないときは次の URL を開く：\n" + url)
    webbrowser.open(url)
    while "code" not in got and "error" not in got:
        srv.handle_request()
    if got.get("state") != state or "code" not in got:
        die("許可が得られなかった：" + str(got.get("error")))
    st, _, body = http("POST", "https://oauth2.googleapis.com/token", urllib.parse.urlencode({
        "code": got["code"], "client_id": c["client_id"], "client_secret": c["client_secret"],
        "redirect_uri": redirect, "grant_type": "authorization_code"}).encode())
    tok = json.loads(body)
    if st != 200 or "refresh_token" not in tok:
        die("トークンを取得できなかった：" + body.decode("utf-8", "replace")[:300])
    TOKEN.write_text(json.dumps({"refresh_token": tok["refresh_token"]}), encoding="utf-8")
    ch = my_channel(tok["access_token"])
    if FORBIDDEN.search(ch["title"]):
        TOKEN.unlink()
        die(f"つながったのは「{ch['title']}」。RE:VERSE には上げない決まりなので、許可を捨てた。新しいチャンネルのアカウントでやり直す")
    CHANNEL.write_text(json.dumps(ch, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"つながったチャンネル：{ch['title']}（{ch['id']}）。publish/channel.json に記録した。以後、このチャンネルにだけ上げる")


def access_token():
    if not TOKEN.exists():
        die("まだ許可していない。python tools/youtube_upload.py auth を実行する")
    c = client()
    st, _, body = http("POST", "https://oauth2.googleapis.com/token", urllib.parse.urlencode({
        "client_id": c["client_id"], "client_secret": c["client_secret"], "grant_type": "refresh_token",
        "refresh_token": json.loads(TOKEN.read_text(encoding="utf-8"))["refresh_token"]}).encode())
    if st != 200:
        die("許可の期限が切れている（auth をやり直す）：" + body.decode("utf-8", "replace")[:300])
    return json.loads(body)["access_token"]


def my_channel(tok):
    st, _, body = http("GET", "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
                       headers={"Authorization": "Bearer " + tok})
    items = json.loads(body).get("items") or []
    if st != 200 or not items:
        die("チャンネルが見つからない（このアカウントで YouTube チャンネルを作ってあるか確かめる）：" + body.decode("utf-8", "replace")[:300])
    return {"id": items[0]["id"], "title": items[0]["snippet"]["title"]}


def guard_channel(tok):
    """上げる直前に毎回、つながっているチャンネルを確かめる。"""
    if not CHANNEL.exists():
        die("publish/channel.json がない（auth を実行する）")
    want = json.loads(CHANNEL.read_text(encoding="utf-8"))
    now = my_channel(tok)
    if FORBIDDEN.search(now["title"]) or FORBIDDEN.search(want["title"]):
        die(f"RE:VERSE には上げない（つながっているチャンネル：{now['title']}）")
    if now["id"] != want["id"]:
        die(f"つながっているチャンネル（{now['title']}）が、記録（{want['title']}）と違う")
    return now


def booked():
    return [json.loads(f.read_text(encoding="utf-8")) for f in LOG.glob("*.json")] if LOG.exists() else []


def status():
    """予約ずみで未公開の本数と、次に空いている 18:00 の枠を表示する（毎日の自動実行が読む）。"""
    now = datetime.datetime.now(JST)
    fut = sorted(r["publishAt"] for r in booked()
                 if datetime.datetime.strptime(r["publishAt"], "%Y-%m-%d %H:%M").replace(tzinfo=JST) > now)
    d = now.date() if now.hour < 17 else now.date() + datetime.timedelta(days=1)
    while f"{d} 18:00" in fut:
        d += datetime.timedelta(days=1)
    print(json.dumps({"connected": TOKEN.exists() and CHANNEL.exists(), "booked_not_yet_public": len(fut),
                      "booked": fut, "next_free_slot": f"{d} 18:00", "max_booked": 10}, ensure_ascii=False))


def setup():
    """設定の案内役。画面を 1 つずつ開き、Enter で次へ進む。ユーザー本人がターミナルで実行する。"""
    def step(n, title, url, lines):
        print(f"\n━━ 手順 {n}／6：{title} ━━")
        for ln in lines:
            print("  ・" + ln)
        if url:
            webbrowser.open(url)
        input("  できたら Enter を押す → ")

    print("automovie の YouTube 自動アップロードの設定を始めます（無料・15 分ほど）。\n"
          "ブラウザは必ず【automovie 用の新しいチャンネルの Google アカウント】でログインしておいてください。")
    step(1, "YouTube のチャンネルを作る", "https://www.youtube.com/account",
         ["開いた画面で「チャンネルを作成」があれば押して、名前を決める", "もうチャンネルがあれば何もしなくてよい"])
    step(2, "Google Cloud のプロジェクトを作る", "https://console.cloud.google.com/projectcreate",
         ["プロジェクト名に automovie と入れて「作成」を押す", "規約の画面が出たら、読んで同意する"])
    step(3, "YouTube の API を使えるようにする", "https://console.cloud.google.com/apis/library/youtube.googleapis.com",
         ["上の帯で、プロジェクトが automovie になっているか見る", "青い「有効にする」を押す"])
    step(4, "アプリの名前を登録する", "https://console.cloud.google.com/auth/overview",
         ["「開始」を押す", "アプリ名：automovie ／ メール：自分のアドレスを選ぶ", "対象：「外部」を選ぶ",
          "連絡先：自分のアドレス → 同意にチェック →「作成」",
          "左の「対象」を開き、「アプリを公開」→「確認」を押す（これをしないと 7 日ごとに止まる）"])
    step(5, "鍵のファイルを作る", "https://console.cloud.google.com/auth/clients/create",
         ["アプリケーションの種類：「デスクトップ アプリ」を選ぶ", "名前はそのままでよい →「作成」",
          "出てきた画面の「JSON をダウンロード」を押す（ダウンロード フォルダに入る）"])
    dl = Path.home() / "Downloads"
    cands = sorted(dl.glob("client_secret*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not SECRET.exists():
        if not cands:
            die(f"ダウンロード フォルダ（{dl}）に client_secret で始まるファイルが見つからない。手順 5 のダウンロードをやり直して、もう一度この案内を実行する")
        cands[0].replace(SECRET)
        print(f"\n  鍵のファイルを所定の場所へ移しました（{SECRET}）。中身は誰にも見せないでください。")
    print("\n━━ 手順 6／6：許可する ━━\n  ・ブラウザが開くので、新しいチャンネルのアカウントを選ぶ\n"
          "  ・「このアプリは Google で確認されていません」と出たら「詳細」→「automovie（安全ではないページ）に移動」\n"
          "  ・チェックを 2 つとも入れて「続行」")
    auth()
    print("\n設定は終わりです。Claude に「設定した」と伝えてください。")


def read_meta(vdir):
    md = (vdir / "youtube_metadata.md").read_text(encoding="utf-8")

    def sec(name):
        m = re.search(rf"^## {name}\s*\n(.*?)(?=^## |\Z)", md, re.S | re.M)
        return m.group(1).strip() if m else ""
    title, desc, setting = sec("タイトル"), sec("説明文"), sec("設定")
    if not title or not desc:
        die("youtube_metadata.md にタイトルか説明文がない")
    if len(title) > 100:
        die("タイトルが 100 字を超えている")
    cat = next((v for k, v in CATEGORY.items() if k in setting), "24")
    synth = bool(re.search(r"合成されたコンテンツ[^\n]*はい", setting))
    tags = [t for t in re.findall(r"#([^\s#]+)", desc) if t.lower() != "shorts"]
    return {"title": title, "description": desc, "categoryId": cat, "tags": tags, "synthetic": synth}


def upload(vdir, at, dry):
    vdir = Path(vdir)
    code = vdir.name
    mp4 = vdir / f"{code}.mp4"
    if not mp4.exists():
        die(f"{mp4} がない")
    qa = vdir / "qa.md"
    if not qa.exists() or "- [ ]" in qa.read_text(encoding="utf-8"):
        die(f"{qa} に未チェックの項目がある（検査を全部通した回だけ上げる）")
    if any(r.get("publishAt") == at for r in booked()):
        die(f"{at} にはもう別の回を予約してある")
    if (LOG / f"{code}.json").exists():
        die(f"{code} はもう上げてある（publish/log/{code}.json）")
    when = datetime.datetime.strptime(at, "%Y-%m-%d %H:%M").replace(tzinfo=JST)
    if when < datetime.datetime.now(JST) + datetime.timedelta(minutes=15):
        die("公開の時刻は 15 分以上先にする")
    m = read_meta(vdir)
    body = {"snippet": {"title": m["title"], "description": m["description"], "tags": m["tags"],
                        "categoryId": m["categoryId"], "defaultLanguage": "ja", "defaultAudioLanguage": "ja"},
            "status": {"privacyStatus": "private", "publishAt": when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "selfDeclaredMadeForKids": False, "containsSyntheticMedia": m["synthetic"], "embeddable": True}}
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print(f"ファイル：{mp4}（{mp4.stat().st_size / 1e6:.1f} MB）／公開：{at}（日本時間）")
    if dry:
        print("（--dry-run：送っていない）")
        return
    tok = access_token()
    ch = guard_channel(tok)
    data = mp4.read_bytes()
    st, hd, b = http("POST", "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=true",
                     json.dumps(body).encode("utf-8"),
                     {"Authorization": "Bearer " + tok, "Content-Type": "application/json; charset=UTF-8",
                      "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(data))})
    loc = hd.get("Location") or hd.get("location")
    if st != 200 or not loc:
        die("上げ始められなかった：" + b.decode("utf-8", "replace")[:500])
    st, _, b = http("PUT", loc, data, {"Authorization": "Bearer " + tok, "Content-Type": "video/mp4"})
    if st not in (200, 201):
        die("送信に失敗：" + b.decode("utf-8", "replace")[:500])
    v = json.loads(b)
    LOG.mkdir(parents=True, exist_ok=True)
    rec = {"code": code, "videoId": v["id"], "url": "https://www.youtube.com/shorts/" + v["id"], "channel": ch,
           "publishAt": at, "privacyStatus": v.get("status", {}).get("privacyStatus"),
           "uploadedAt": datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M")}
    (LOG / f"{code}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print("上げた：", json.dumps(rec, ensure_ascii=False))
    if v.get("status", {}).get("publishAt") is None:
        print("注意：予約の時刻が付いていない。YouTube Studio で公開の設定を確かめる（API の審査前は非公開のままになることがある）")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["setup", "auth", "check", "status", "upload"])
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--at", help='公開の時刻（日本時間） "YYYY-MM-DD HH:MM"')
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    PUB.mkdir(exist_ok=True)
    if a.cmd == "setup":
        setup()
    elif a.cmd == "status":
        status()
    elif a.cmd == "auth":
        auth()
    elif a.cmd == "check":
        print(json.dumps(guard_channel(access_token()), ensure_ascii=False))
    else:
        if not a.dir or not a.at:
            die("upload には 回のフォルダ と --at が要る")
        upload(a.dir, a.at, a.dry_run)
