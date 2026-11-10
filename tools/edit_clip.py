"""実写の素材＋ナレーションのショートを組み立てる（黒地・上に 2 行の題・中央に映像・字幕）。

python tools/edit_clip.py videos/004 base     素材を切って並べる（work/base.mp4、音なし）
python tools/edit_clip.py videos/004 audio    自作 BGM と声を混ぜて −14 LUFS にする（work/mix.wav）
python tools/edit_clip.py videos/004 stills 1,5,12   文字を重ねたコマを work/stills/ に出す
python tools/edit_clip.py videos/004 render   完成版を書き出す（videos/NNN/NNN.mp4）

script.json：title（2 行）、credit、source、crop、blocks（from＝その行から、src＝素材の [開始, 終了] 秒）。
素材の音は使わない（元の動画に付いている音楽の権利が分からないため）。
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 48000
VID_Y = 400                     # 映像を置く位置（上端）
CX = 500                        # 字幕の中心（右のボタンを避けて少し左）
YEL, WHITE = (255, 200, 40), (255, 255, 255)
_fc = {}


def F(size, weight="Black"):
    if (size, weight) not in _fc:
        f = ImageFont.truetype("C:/Windows/Fonts/NotoSansJP-VF.ttf", size)
        f.set_variation_by_name(weight)
        _fc[(size, weight)] = f
    return _fc[(size, weight)]


def fit(s, size, maxw):
    while size > 30 and max(F(size).getlength(p) for p in s.split("\n")) > maxw:
        size -= 2
    return size


class Job:
    def __init__(self, vdir):
        self.dir = Path(vdir)
        self.work = self.dir / "work"
        self.sc = json.loads((self.dir / "script.json").read_text(encoding="utf-8"))
        self.T = json.loads((self.work / "timing.json").read_text(encoding="utf-8"))
        self.total = self.T["total"]
        self.L = {ln["id"]: ln for ln in self.T["lines"]}
        cw, ch = (int(x) for x in self.sc["crop"].split(":")[:2])
        self.vh = round(ch * W / cw)
        self.static = self._static()

    # ---- 映像の土台 ----
    def base(self):
        bl = self.sc["blocks"]
        starts = [0.0] + [self.L[b["from"]]["start"] - 0.08 for b in bl[1:]] + [self.total]
        parts, n = [], 0
        for i, b in enumerate(bl):
            need = starts[i + 1] - starts[i]
            segs = [list(s) for s in b["src"]]
            have = sum(e - s for s, e in segs)
            if have > need:                       # 素材が長い → 最後を切る
                segs[-1][1] -= have - need
                speed = 1.0
            else:                                 # 素材が短い → ゆっくり再生（最大 0.6 倍速まで）
                speed = max(0.6, have / need)
            for s, e in segs:
                parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=(PTS-STARTPTS)/{speed:.4f}[p{n}]")
                n += 1
            print(f"{b['from']}: 必要 {need:.2f}s 素材 {have:.2f}s 速さ {speed:.2f}")
        fc = ";".join(parts) + ";" + "".join(f"[p{i}]" for i in range(n)) + (
            f"concat=n={n}:v=1:a=0,fps={FPS},crop={self.sc['crop']},scale={W}:{self.vh},"
            f"eq=contrast=1.06:saturation=1.12,pad={W}:{H}:0:{VID_Y}:black,"
            f"tpad=stop_mode=clone:stop_duration=3,trim=0:{self.total:.3f}[v]")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(self.dir / self.sc["source"]),
                        "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                        "-pix_fmt", "yuv420p", str(self.work / "base.mp4")], check=True)

    # ---- 文字 ----
    def _static(self):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        t1, t2 = self.sc["title"]
        s1, s2 = fit(t1, 104, 1000), fit(t2, 104, 1000)
        d.text((W / 2, 120), t1, font=F(s1), fill=WHITE, anchor="ma")
        d.text((W / 2, 120 + s1 + 22), t2, font=F(s2), fill=YEL, anchor="ma")
        d.text((W / 2, VID_Y + self.vh + 14), self.sc["credit"], font=F(26, "Medium"), fill=(190, 190, 190), anchor="ma")
        return im

    def overlay(self, t):
        im = self.static.copy()
        d = ImageDraw.Draw(im)
        for ln in self.T["lines"]:
            for s in ln["subs"]:
                if s["start"] <= t < s["end"]:
                    txt = s["text"]
                    k = min(1.0, (t - s["start"]) / 0.1)          # 出はじめに少しだけ弾む
                    size = int(fit(txt, 78, 820) * (0.9 + 0.1 * k))
                    n = txt.count("\n") + 1
                    y = VID_Y + self.vh - 150 - n * size * 1.15
                    d.multiline_text((CX, y), txt, font=F(size), fill=WHITE, anchor="ma", align="center",
                                     spacing=int(size * 0.15), stroke_width=11, stroke_fill=(0, 0, 0, 255))
                    return im
        return im

    # ---- 音 ----
    def audio(self):
        with wave.open(str(self.work / "voice.wav")) as w:
            v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        n = len(v)
        tt = np.arange(n) / SR
        rng = np.random.default_rng(11)
        bgm = np.zeros(n, dtype=np.float32)
        # 自作の BGM：あたたかい長調の和音（C→G→Am→F を 4 秒ずつ）と、やわらかい拍
        chords = [(130.81, 164.81, 196.00, 261.63), (98.00, 146.83, 196.00, 246.94),
                  (110.00, 164.81, 220.00, 261.63), (87.31, 130.81, 174.61, 220.00)]
        bar = 4.0
        for i in range(int(n / SR / bar) + 1):
            i0 = int(i * bar * SR)
            m = min(n - i0, int((bar + 1.0) * SR))
            if m <= 0:
                break
            x = np.arange(m) / SR
            env = np.clip(x / 0.6, 0, 1) * np.clip((bar + 1.0 - x) / 1.0, 0, 1)
            for f in chords[i % 4]:
                for det in (-0.4, 0.4):
                    bgm[i0:i0 + m] += env * (np.sin(2 * np.pi * (f + det) * x + rng.random() * 6)
                                             + 0.3 * np.sin(2 * np.pi * 2 * (f + det) * x))
            for beat in range(4):                # ピアノ風の単音を 1 秒ごと
                j0 = i0 + int(beat * SR)
                mm = min(n - j0, int(1.2 * SR))
                if mm <= 0:
                    break
                xx = np.arange(mm) / SR
                f = chords[i % 4][(beat * 2 + 1) % 4] * 2
                bgm[j0:j0 + mm] += 2.4 * np.exp(-xx * 3.5) * (np.sin(2 * np.pi * f * xx) + 0.4 * np.sin(2 * np.pi * 2 * f * xx))
        bgm /= np.max(np.abs(bgm))
        fade = np.clip(tt / 0.3, 0, 1) * np.clip((n / SR - tt) / 0.8, 0, 1)
        mix = v * 0.9 + bgm * 0.11 * fade
        mix = np.clip(mix / max(1.0, np.max(np.abs(mix))), -1, 1)
        pre = self.work / "premix.wav"
        with wave.open(str(pre), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((mix * 32767).astype(np.int16).tobytes())
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre), "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        i_now = float(r.stderr[r.stderr.rindex("I:") + 2:].split("LUFS")[0])
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(pre),
                        "-af", f"volume={-14.0 - i_now:.2f}dB,alimiter=limit=0.84", "-ar", str(SR), "-ac", "2",
                        str(self.work / "mix.wav")], check=True)
        print(f"mix.wav（元 {i_now} LUFS → −14 に調整）")

    def render(self):
        out = self.dir / f"{self.dir.name}.mp4"
        n = int(round(self.total * FPS))
        p = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(self.work / "base.mp4"),
             "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
             "-i", str(self.work / "mix.wav"),
             "-filter_complex", "[0:v][1:v]overlay=shortest=1,format=yuv420p[v]", "-map", "[v]", "-map", "2:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-c:a", "aac", "-b:a", "192k", "-t", f"{self.total:.3f}", "-movflags", "+faststart", str(out)],
            stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(self.overlay(i / FPS).tobytes())
        p.stdin.close()
        p.wait()
        print("書き出し完了", out)

    def stills(self, times):
        (self.work / "stills").mkdir(exist_ok=True)
        for t in times:
            r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t}", "-i", str(self.work / "base.mp4"),
                                "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True)
            fr = Image.frombytes("RGBA", (W, H), r.stdout)
            fr.alpha_composite(self.overlay(t))
            fr.convert("RGB").resize((432, 768), Image.LANCZOS).save(self.work / "stills" / f"t{t:05.1f}.png")


if __name__ == "__main__":
    job = Job(sys.argv[1])
    cmd = sys.argv[2]
    if cmd == "base":
        job.base()
    elif cmd == "audio":
        job.audio()
    elif cmd == "stills":
        job.stills([float(x) for x in sys.argv[3].split(",")])
    elif cmd == "render":
        job.render()
