"""ナレーションを VOICEVOX で作る。

使い方: python tools/voice.py videos/001
script.json を読み、work/voice.wav（全体）と work/timing.json（行と字幕の時刻）を書く。
読み（カナ）を work/reading.txt に残すので、読み間違いはそこで確かめる。
"""
import io
import json
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np

ENGINE = "http://127.0.0.1:50021"
SR = 48000


def post(path, params, body=None):
    url = ENGINE + path + "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode("utf-8") if body is not None else b""
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def chunk_times(query):
    """読点・句点（pause_mora）で区切った各かたまりの (開始, 終了) 秒。"""
    sp = query["speedScale"]
    t = query["prePhonemeLength"] / sp
    out, start = [], t
    phrases = query["accent_phrases"]
    for i, ph in enumerate(phrases):
        for m in ph["moras"]:
            t += ((m.get("consonant_length") or 0) + m["vowel_length"]) / sp
        pm = ph.get("pause_mora")
        if pm:
            out.append((start, t))
            t += pm["vowel_length"] / sp
            start = t
        elif i == len(phrases) - 1:
            out.append((start, t))
    return out


def main(vdir):
    vdir = Path(vdir)
    sc = json.loads((vdir / "script.json").read_text(encoding="utf-8"))
    work = vdir / "work"
    work.mkdir(exist_ok=True)
    pcm, timing, reading, t0 = [], [], [], 0.25
    pcm.append(np.zeros(int(t0 * SR), dtype=np.int16))
    for ln in sc["lines"]:
        q = json.loads(post("/audio_query", {"text": ln["say"], "speaker": sc["speaker"]}))
        q.update(speedScale=sc["speed"], outputSamplingRate=SR, outputStereo=False,
                 prePhonemeLength=0.05, postPhonemeLength=0.05, intonationScale=1.15)
        for k, v in ln.get("query", {}).items():
            q[k] = v
        wav = post("/synthesis", {"speaker": sc["speaker"]}, q)
        with wave.open(io.BytesIO(wav)) as w:
            assert w.getframerate() == SR and w.getnchannels() == 1
            a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        ct = chunk_times(q)
        if len(ct) != len(ln["subs"]):
            raise SystemExit(f"{ln['id']}: 音声の区切り {len(ct)} と字幕 {len(ln['subs'])} の数が合わない\n{q['kana']}")
        dur = len(a) / SR
        subs = []
        for i, (s, e) in enumerate(ct):
            end = ct[i + 1][0] if i + 1 < len(ct) else dur
            subs.append({"text": ln["subs"][i], "start": round(t0 + s, 3), "end": round(t0 + end, 3)})
        timing.append({"id": ln["id"], "start": round(t0, 3), "end": round(t0 + dur, 3), "subs": subs})
        reading.append(f"{ln['id']}: {ln['say']}\n    {q['kana']}")
        pcm.append(a)
        pcm.append(np.zeros(int(sc["gap"] * SR), dtype=np.int16))
        t0 += dur + sc["gap"]
    pcm.append(np.zeros(int(0.9 * SR), dtype=np.int16))
    allpcm = np.concatenate(pcm)
    with wave.open(str(work / "voice.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(allpcm.tobytes())
    total = len(allpcm) / SR
    (work / "timing.json").write_text(json.dumps({"total": round(total, 3), "lines": timing},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    (work / "reading.txt").write_text("\n".join(reading), encoding="utf-8")
    print("\n".join(reading))
    print(f"全体 {total:.2f} 秒")


if __name__ == "__main__":
    main(sys.argv[1])
