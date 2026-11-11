"""伸びているショートの「公開されている情報」だけを集める（動画そのものは取得しない）。

python tools/collect_shorts.py search   検索結果から 題名・再生数・ID を集める → research/data/shorts_raw.json
python tools/collect_shorts.py detail   再生数の多い順に、各ショートのページから チャンネル・公開日・尺・説明文 を足す
python tools/collect_shorts.py export   research/data/shorts.csv に書き出す
python tools/collect_shorts.py weekly   週に 1 度の収集を全部まとめて行う（2,000 本以上。30〜40 分かかる）

ログインも API キーも使わない。1 回ごとに間をあけてゆっくり読む。
"""
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA = Path(__file__).parent.parent / "research" / "data"
RAW = DATA / "shorts_raw.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
      "Accept-Language": "ja"}

QUERIES = {
    "スポーツ": ["スポーツ 名場面 shorts", "神プレー shorts", "スーパープレー shorts", "野球 珍プレー shorts", "大谷翔平 shorts",
              "サッカー スーパーゴール shorts", "バスケ 神プレー shorts", "格闘技 KO shorts", "ボクシング 衝撃 shorts",
              "陸上 逆転 shorts", "オリンピック 感動 shorts", "スポーツ ハプニング shorts", "スポーツ 感動 shorts",
              "スポーツ ランキング shorts", "プロ野球 好プレー shorts", "卓球 ラリー shorts", "バレー スパイク shorts",
              "相撲 shorts", "F1 クラッシュ shorts", "体操 神技 shorts"],
    "海外・感動": ["海外 感動 shorts", "泣ける話 shorts", "感動する話 海外 shorts", "涙が止まらない shorts", "海外 いい話 shorts",
               "動物 救助 shorts", "保護犬 感動 shorts", "再会 感動 shorts", "優しい世界 shorts", "海外 サプライズ 感動 shorts"],
    "海外・笑える": ["海外 おもしろ shorts", "笑える動画 shorts", "海外 ハプニング shorts", "おもしろ動画 shorts", "爆笑 shorts",
                "ドッキリ 海外 shorts", "失敗 おもしろ shorts", "動物 おもしろ shorts", "猫 おもしろ shorts", "赤ちゃん おもしろ shorts"],
    "衝撃・すごい": ["衝撃映像 shorts", "海外 衝撃 shorts", "奇跡の瞬間 shorts", "危機一髪 shorts", "神業 shorts",
                "職人技 shorts", "ドライブレコーダー shorts", "すごい人 shorts", "世界のすごい shorts", "スカッとする話 shorts"],
    "解説・雑学": ["雑学 shorts", "海外の反応 shorts", "宇宙 shorts", "動物 雑学 shorts", "ランキング shorts",
               "世界の国 比較 shorts", "歴史 雑学 shorts", "都市伝説 shorts", "お金 雑学 shorts", "心理学 shorts"],
    "追加（週次で 2,000 本以上にするため）": [
        "救助 感動 shorts", "消防士 救助 shorts", "警察官 感動 shorts", "軍人 帰還 サプライズ shorts", "犬 感動 shorts",
        "野生動物 衝撃 shorts", "海の生き物 shorts", "自然 絶景 shorts", "宇宙 映像 shorts", "ロケット 打ち上げ shorts",
        "災害 映像 shorts", "台風 映像 shorts", "飛行機 着陸 shorts", "戦闘機 shorts", "船 嵐 shorts",
        "ヘリコプター 救助 shorts", "沿岸警備隊 shorts", "子供 優しい shorts", "親切 海外 shorts", "ヒーロー 一般人 shorts",
        "昔の映像 shorts", "歴史 映像 カラー化 shorts", "工場 製造 shorts", "巨大 重機 shorts", "天気 雷 shorts"],
}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def views(txt):
    m = re.search(r"([\d,.]+)\s*(万|億)?\s*回視聴", txt)
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    return int(n * {"万": 1e4, "億": 1e8, None: 1}[m.group(2)])


def walk(o, out):
    if isinstance(o, dict):
        v = o.get("shortsLockupViewModel")
        if v:
            out.append(v)
        for x in o.values():
            walk(x, out)
    elif isinstance(o, list):
        for x in o:
            walk(x, out)


def load():
    return json.loads(RAW.read_text(encoding="utf-8")) if RAW.exists() else {}


def save(db):
    DATA.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(db, ensure_ascii=False, indent=0), encoding="utf-8")


def search():
    db = load()
    for cat, qs in QUERIES.items():
        for q in qs:
            try:
                h = get("https://www.youtube.com/results?search_query=" + urllib.parse.quote(q) + "&hl=ja&gl=JP")
                d = json.loads(re.search(r"var ytInitialData = (\{.*?\});</script>", h, re.S).group(1))
            except Exception as e:
                print("失敗", q, e, flush=True)
                time.sleep(5)
                continue
            items = []
            walk(d, items)
            new = 0
            for it in items:
                vid = it["onTap"]["innertubeCommand"].get("reelWatchEndpoint", {}).get("videoId")
                acc = it.get("accessibilityText", "")
                if not vid:
                    continue
                title = re.sub(r"[,、]\s*[\d,.]+\s*(万|億)?\s*回視聴.*$", "", acc)
                if vid not in db:
                    db[vid] = {"id": vid, "title": title, "views": views(acc), "category": cat, "queries": [q]}
                    new += 1
                elif q not in db[vid]["queries"]:
                    db[vid]["queries"].append(q)
            print(f"{cat} | {q} | {len(items)} 件（新規 {new}） 合計 {len(db)}", flush=True)
            save(db)
            time.sleep(1.5)


def detail(limit=700, min_views=100000):
    db = load()
    todo = sorted((v for v in db.values() if (v["views"] or 0) >= min_views and "channel" not in v and not v.get("detail_failed")),
                  key=lambda v: -v["views"])[:limit]
    print("詳細を読む本数", len(todo), flush=True)
    for i, v in enumerate(todo):
        try:
            h = get("https://www.youtube.com/shorts/" + v["id"] + "?hl=ja&gl=JP")
            pr = json.loads(re.search(r"var ytInitialPlayerResponse = (\{.*?\});(?:var|</script>)", h, re.S).group(1))
            vd = pr.get("videoDetails", {})
            mf = pr.get("microformat", {}).get("playerMicroformatRenderer", {})
            v.update(channel=vd.get("author"), channel_id=vd.get("channelId"),
                     seconds=int(vd.get("lengthSeconds") or 0), published=(mf.get("publishDate") or "")[:10],
                     views_exact=int(vd.get("viewCount") or 0), keywords=(vd.get("keywords") or [])[:12],
                     description=(vd.get("shortDescription") or "")[:400], genre=mf.get("category"))
            if not vd.get("author"):
                v["detail_failed"] = True
        except Exception as e:
            v["detail_failed"] = True
            print("失敗", v["id"], str(e)[:80], flush=True)
        if i % 25 == 0:
            print(i, "/", len(todo), flush=True)
            save(db)
        time.sleep(1.0)
    save(db)


SOUND_RE = re.compile(r"titleFormatted\\x22:\\x7b\\x22content\\x22:\\x22((?:(?!\\x22\\x7d).)*)\\x22\\x7d,\\x22iconImage\\x22:"
                      r"\\x7b\\x22clientResource\\x22:\\x7b\\x22imageName\\x22:\\x22MUSIC_NOTE_SYMBOL")


def sound(limit=250):
    """再生数の多い順に、各ショートのページに出ている使用曲の名前を足す（曲そのものは取得しない）。"""
    db = load()
    todo = sorted((v for v in db.values() if "sound" not in v), key=lambda v: -(v.get("views") or 0))[:limit]
    for i, v in enumerate(todo):
        try:
            h = get("https://www.youtube.com/shorts/" + v["id"] + "?hl=ja&gl=JP")
            m = SOUND_RE.search(h)
            s = m.group(1) if m else ""
            v["sound"] = re.sub(r"\\x([0-9a-f]{2})", lambda g: chr(int(g.group(1), 16)), s).encode("latin-1", "ignore").decode("utf-8", "ignore") if "\\x" in s else s
        except Exception as e:
            print("失敗", v["id"], str(e)[:80], flush=True)
        if i % 25 == 0:
            print(i, "/", len(todo), flush=True)
            save(db)
        time.sleep(1.0)
    save(db)


def weekly():
    """週に 1 度の収集。前回のデータを日付つきで残し、新しく集め直す。"""
    import datetime
    if RAW.exists():
        RAW.replace(DATA / f"shorts_raw_until_{datetime.date.today()}.json")
    search()
    n = len(load())
    print("集めた本数", n, flush=True)
    detail(limit=700)
    sound(limit=250)
    export()
    if n < 2000:
        print(f"注意：{n} 本で、目標の 2,000 本に足りない。QUERIES に検索語を足す")


def export():
    db = load()
    rows = sorted(db.values(), key=lambda v: -(v.get("views") or 0))
    with open(DATA / "shorts.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["順位", "再生数", "題名", "チャンネル", "公開日", "秒", "分類（検索の系統）", "URL", "検索語", "タグ", "説明文（先頭）", "使用曲（ページの表示）"])
        for i, v in enumerate(rows, 1):
            w.writerow([i, v.get("views_exact") or v.get("views"), v["title"], v.get("channel", ""), v.get("published", ""),
                        v.get("seconds", ""), v["category"], "https://www.youtube.com/shorts/" + v["id"],
                        " / ".join(v["queries"]), " ".join(v.get("keywords", [])),
                        (v.get("description", "") or "").replace("\n", " ")[:200], v.get("sound", "")])
    print("shorts.csv", len(rows), "本")


if __name__ == "__main__":
    {"search": search, "detail": detail, "sound": sound, "export": export, "weekly": weekly}[sys.argv[1]]()
