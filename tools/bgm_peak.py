"""BGM のどこから使うかを決める手伝い。曲の盛り上がり（音の大きさ）を 1 秒ごとに測る。

使い方:
    python -X utf8 tools/bgm_peak.py videos/NNN/assets/曲.mp3 41.5 [山場の秒]

  41.5   動画の長さ（秒）
  山場   動画の中でいちばん盛り上げたい時刻（秒）。省くと動画の 7 割の位置。

出力: 1 秒ごとの大きさの棒、曲のいちばん盛り上がる所、
      その盛り上がりが動画の山場に来るような "start"（script.json の bgm.start に書く値）。
音は聞けないので、分かるのは大きさの変化だけ。曲の雰囲気は配布元の説明で判断する。
"""
import subprocess
import sys

import numpy as np

SR = 8000


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    path, dur = sys.argv[1], float(sys.argv[2])
    climax = float(sys.argv[3]) if len(sys.argv) > 3 else dur * 0.7
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path,
         "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    secs = len(x) // SR
    rms = np.array([np.sqrt(np.mean(x[i * SR:(i + 1) * SR] ** 2) + 1e-12) for i in range(secs)])
    db = 20 * np.log10(rms)
    top = db.max()
    for i, v in enumerate(db):
        print(f"{i:4d}s {v:6.1f} dB {'#' * max(0, int((v - top + 30) / 1.5))}")
    # 盛り上がり：直前 4 秒より大きく上がり、その後 6 秒の平均が大きい所
    best, best_score = 0, -1e9
    for i in range(4, secs - 6):
        score = (db[i:i + 6].mean() - db[i - 4:i].mean()) + 0.5 * (db[i:i + 6].mean() - db.mean())
        if score > best_score:
            best, best_score = i, score
    start = best - climax
    print(f"曲の長さ {secs} 秒／いちばん盛り上がる所 {best} 秒あたり")
    if start < 0 or start + dur > secs:
        start = min(max(0.0, start), max(0.0, secs - dur))
        print("（盛り上がりを山場にぴったりは合わせられない。入る範囲に寄せた）")
    print(f'動画の山場 {climax:.1f} 秒に合わせるなら "start": {start:.1f}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
