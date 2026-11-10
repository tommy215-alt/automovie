"""Wikimedia Commons で、再利用できる動画を探す（ライセンスも表示）。
python tools/commons_search.py "検索語1" "検索語2" ...   （filetype:video は自動で付く）
"""
import json
import re
import sys
import urllib.parse
import urllib.request


def search(s, n=20):
    u = ("https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6"
         f"&gsrlimit={n}&gsrsearch={urllib.parse.quote('filetype:video ' + s)}"
         "&prop=imageinfo&iiprop=size|extmetadata|url")
    req = urllib.request.Request(u, headers={"User-Agent": "asset-license-check/1.0"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    for p in pages:
        i = p["imageinfo"][0]
        m = i["extmetadata"]
        g = lambda k: re.sub("<[^>]+>", "", m.get(k, {}).get("value", "")).strip().replace("\n", " ")[:50]
        print(f"{p['title'][5:90]} | {i.get('duration', 0):.0f}s {i['width']}x{i['height']} | {g('LicenseShortName')} | {g('Artist')}")


if __name__ == "__main__":
    for s in sys.argv[1:]:
        print("##", s)
        search(s)
