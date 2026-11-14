"""完成した動画の音声を、耳の代わりに機械で確かめる。

使い方:
    python -X utf8 tools/check_audio.py videos/NNN

やること:
  1. 完成版（NNN.mp4、BGM 入り）の音声を行ごとに切り出し、音声認識（faster-whisper）で文字に起こす。
  2. 台本の読み（say）と、起こした文字を、どちらも VOICEVOX でカナにして比べる（一致率）。
     BGM を混ぜた音から起こすので、「声が BGM に埋もれず言葉として届くか」の検査になる。
  3. 行ごとの話す速さ（1 秒あたりのカナの数）、行の間の空き、音割れを測る。
  4. 結果を videos/NNN/work/qa/audio_check.json に書き、要約を表示する。
     1 つでも不合格なら終了コード 1。

音声認識は CPU で動かす（GPU は RE:VERSE と書き出しのために空けておく）。
分からないこと: 抑揚の自然さ、BGM の雰囲気が合うか。これは人が聞かないと判断できない。
"""
import difflib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

VOICEVOX = "http://127.0.0.1:50021"
MODEL = "small"          # CPU で 40 秒の音声が 1 分ほど
MIN_MATCH = 0.80         # カナの一致率。これ未満は不合格
MAX_RATE = 9.5           # 1 秒あたりのカナ数。これを超えると早口
MAX_GAP = 1.2            # 行の間の空き（秒）。これを超えると間のびする
PAD = 0.12               # 切り出しの前後の余白（秒）


def kana(text: str, speaker: int) -> str:
    """VOICEVOX に読ませたときのカナ（記号を除く）。"""
    text = text.strip()
    if not text:
        return ""
    url = f"{VOICEVOX}/audio_query?speaker={speaker}&text={urllib.parse.quote(text)}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        q = json.loads(r.read().decode("utf-8"))
    return re.sub(r"[^ァ-ヶー]", "", q.get("kana", ""))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    vdir = Path(sys.argv[1])
    code = vdir.name
    mp4 = vdir / f"{code}.mp4"
    script = json.loads((vdir / "script.json").read_text(encoding="utf-8"))
    timing = json.loads((vdir / "work" / "timing.json").read_text(encoding="utf-8"))
    speaker = int(script.get("speaker", 13))
    says = {ln["id"]: ln["say"] for ln in script["lines"]}
    out_dir = vdir / "work" / "qa"
    out_dir.mkdir(parents=True, exist_ok=True)
    wav = out_dir / "final_16k.wav"

    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(mp4),
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)],
        check=True,
    )

    import numpy as np
    from faster_whisper import WhisperModel

    with wave.open(str(wav), "rb") as w:
        sr = w.getframerate()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    audio = pcm.astype(np.float32) / 32768.0
    clipped = int((np.abs(pcm) >= 32700).sum())

    model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    rows, bad = [], []
    prev_end = None
    for ln in timing["lines"]:
        a = max(0.0, ln["start"] - PAD)
        b = min(len(audio) / sr, ln["end"] + PAD)
        seg = audio[int(a * sr):int(b * sr)]
        segs, _ = model.transcribe(seg, language="ja", beam_size=5,
                                   condition_on_previous_text=False)
        heard = "".join(s.text for s in segs).strip()
        want_k = kana(says[ln["id"]], speaker)
        heard_k = kana(heard, speaker)
        match = difflib.SequenceMatcher(None, want_k, heard_k).ratio() if want_k else 0.0
        dur = ln["end"] - ln["start"]
        rate = len(want_k) / dur if dur > 0 else 0.0
        gap = None if prev_end is None else round(ln["start"] - prev_end, 2)
        prev_end = ln["end"]
        problems = []
        if match < MIN_MATCH:
            problems.append(f"聞き取りの一致率が低い（{match:.2f}）")
        if rate > MAX_RATE:
            problems.append(f"早口（1 秒に {rate:.1f} 字）")
        if gap is not None and gap > MAX_GAP:
            problems.append(f"前の行との間が長い（{gap} 秒）")
        row = {"id": ln["id"], "say": says[ln["id"]], "heard": heard,
               "match": round(match, 3), "kana_per_sec": round(rate, 2),
               "gap_before": gap, "problems": problems}
        rows.append(row)
        if problems:
            bad.append(row)
        mark = "×" if problems else "○"
        print(f"{mark} {ln['id']}: 一致 {match:.2f}／1 秒に {rate:.1f} 字／聞こえた文「{heard}」")
        for p in problems:
            print(f"    → {p}")

    if clipped > 20:
        bad.append({"id": "(全体)", "problems": [f"音割れの疑い（最大値のサンプルが {clipped} 個）"]})
        print(f"× 音割れの疑い（最大値のサンプルが {clipped} 個）")

    result = {"video": code, "model": f"faster-whisper {MODEL} (cpu)",
              "min_match": MIN_MATCH, "lines": rows, "clipped_samples": clipped,
              "ok": not bad}
    (out_dir / "audio_check.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    avg = sum(r["match"] for r in rows) / len(rows) if rows else 0.0
    print(f"平均の一致率 {avg:.2f}／不合格 {len(bad)} 件 → {'合格' if not bad else '不合格'}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
