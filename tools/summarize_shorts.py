"""集めたショートの集計を表示する。 python tools/summarize_shorts.py [上位の本数]"""
import collections
import json
import re
import sys
from pathlib import Path

db = list(json.loads((Path(__file__).parent.parent / "research/data/shorts_raw.json").read_text(encoding="utf-8")).values())
TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 12
V = lambda v: v.get("views_exact") or v.get("views") or 0
man = lambda n: f"{n / 1e4:,.0f}万"

print("全体", len(db), "本 / 10万以上", sum(V(v) >= 1e5 for v in db), "/ 100万以上", sum(V(v) >= 1e6 for v in db),
      "/ 1000万以上", sum(V(v) >= 1e7 for v in db), "/ 詳細あり", sum("channel" in v for v in db))
print("\n## 系統ごと（100万以上の本数・中央値）")
for cat in sorted({v["category"] for v in db}):
    vs = sorted(V(v) for v in db if v["category"] == cat)
    print(f"{cat}: {len(vs)} 本, 100万以上 {sum(x >= 1e6 for x in vs)}, 中央値 {man(vs[len(vs) // 2])}")
print("\n## 検索語ごとの中央値（上位 25）")
byq = collections.defaultdict(list)
for v in db:
    byq[v["queries"][0]].append(V(v))
for q, vs in sorted(byq.items(), key=lambda kv: -sorted(kv[1])[len(kv[1]) // 2])[:25]:
    vs.sort()
    print(f"{man(vs[len(vs) // 2]):>8} {q}（{len(vs)} 本, 最大 {man(vs[-1])}）")
for cat in sorted({v["category"] for v in db}):
    print("\n==", cat)
    for v in sorted((v for v in db if v["category"] == cat), key=lambda v: -V(v))[:TOP]:
        print(f"{man(V(v)):>9} | {v.get('seconds', '?')}秒 | {v.get('published', '')} | {(v.get('channel') or '')[:16]} | {v['title'][:56]}")

det = [v for v in db if "channel" in v]
if det:
    print("\n## 尺の分布（詳細あり）")
    b = collections.Counter(min(v["seconds"] // 10 * 10, 180) for v in det)
    for k in sorted(b):
        print(f"{k:>3}〜 秒: {b[k]}")
    print("\n## 公開年")
    print(sorted(collections.Counter(v["published"][:4] for v in det).items()))
    print("\n## よく出るチャンネル（3 本以上）")
    ch = collections.Counter(v["channel"] for v in det)
    for c, n in ch.most_common(40):
        if n >= 3:
            vs = [V(v) for v in det if v["channel"] == c]
            print(f"{n} 本 合計 {man(sum(vs))} | {c}")
    print("\n## 題名の型（詳細ありの中で）")
    pats = {"【】つき": r"【.+?】", "数字（TOP・◯選・位）": r"(TOP|top|選|位|ランキング)", "問いかけ ？": r"[?？]",
            "#タグ入り": r"#", "絵文字": r"[\U0001F300-\U0001FAFF]", "「衝撃・神・ヤバ」": r"(衝撃|神|ヤバ|やば|奇跡|まさか)",
            "「感動・泣」": r"(感動|泣|涙)", "「笑・爆笑・おもしろ」": r"(笑|おもしろ|面白|ww)"}
    for k, p in pats.items():
        print(f"{k}: {sum(bool(re.search(p, v['title'])) for v in det)} / {len(det)}")
    print("\n## 説明文・タグから見た素材の手がかり")
    src = {"引用・出典・credit の記載": r"(引用|出典|credit|Credit|クレジット|source|Source|©|提供)",
           "TikTok / Instagram の記載": r"(tiktok|TikTok|instagram|Instagram|インスタ)",
           "公式（チャンネル名・説明に 公式/Official）": r"(公式|Official|official)",
           "VOICEVOX・音読さん など合成音声の記載": r"(VOICEVOX|voicevox|音読さん|CoeFont|ずんだもん|VOICEPEAK)",
           "切り抜き の記載": r"切り抜き", "AI の記載": r"(AI|ＡＩ|生成)"}
    for k, p in src.items():
        print(f"{k}: {sum(bool(re.search(p, (v.get('description') or '') + ' ' + (v.get('channel') or '') + ' ' + ' '.join(v.get('keywords', [])))) for v in det)} / {len(det)}")
