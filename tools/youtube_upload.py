"""YouTube へ予約つきで上げる道具（Python の標準機能だけ。追加のインストールなし）。

  python tools/youtube_upload.py auth                      最初の 1 回。ブラウザで許可する（ユーザー本人が実行する）
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
    ap.add_argument("cmd", choices=["auth", "check", "upload"])
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--at", help='公開の時刻（日本時間） "YYYY-MM-DD HH:MM"')
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    PUB.mkdir(exist_ok=True)
    if a.cmd == "auth":
        auth()
    elif a.cmd == "check":
        print(json.dumps(guard_channel(access_token()), ensure_ascii=False))
    else:
        if not a.dir or not a.at:
            die("upload には 回のフォルダ と --at が要る")
        upload(a.dir, a.at, a.dry_run)
