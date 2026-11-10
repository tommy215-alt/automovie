"""001 を描いて書き出す。

python videos/001/make.py audio          BGM を作って声と混ぜる（work/mix.wav）
python videos/001/make.py stills 1,9,20  その秒のコマを work/stills/ に出す
python videos/001/make.py render         work/001.mp4 を書き出す
"""
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
WORK = HERE / "work"
AS = HERE / "assets"
W, H, FPS = 1080, 1920, 30
SR = 48000
T = json.loads((WORK / "timing.json").read_text(encoding="utf-8"))
TOTAL = T["total"]
L = {ln["id"]: ln for ln in T["lines"]}
ORDER = [ln["id"] for ln in T["lines"]]

# 字幕と図を置いてよい範囲（YouTube の右のボタンと下の題名を避ける）
CX = 500            # 文字の中心（右のボタンのぶん左へ寄せる）
SUB_Y = 1340
SAFE_R = 930

YEL = (255, 214, 64)
WHITE = (255, 255, 255)
CYAN = (120, 220, 255)
GRAY = (170, 180, 200)

FONTS = "C:/Windows/Fonts/"


def font(size, weight="Black"):
    f = ImageFont.truetype(FONTS + "NotoSansJP-VF.ttf", size)
    f.set_variation_by_name(weight)
    return f


_fc = {}


def F(size, weight="Black"):
    k = (size, weight)
    if k not in _fc:
        _fc[k] = font(size, weight)
    return _fc[k]


# ---------- 小さな道具 ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ramp(t, t0, d=0.35):
    """t0 から d 秒かけて 0→1。"""
    return ease((t - t0) / d)


def sub_start(line, i):
    return L[line]["subs"][i]["start"]


def circle_img(path, d, bright=1.0):
    im = Image.open(path).convert("RGB")
    bb = im.convert("L").point(lambda v: 255 if v > 28 else 0).getbbox()   # 黒い余白を落とす
    if bb:
        im = im.crop(bb)
    s = min(im.size)
    l, tp = (im.width - s) // 2, (im.height - s) // 2
    im = im.crop((l, tp, l + s, tp + s)).resize((d, d), Image.LANCZOS)
    if bright != 1.0:
        im = Image.eval(im, lambda v: min(255, int(v * bright)))
    m = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(m).ellipse((6, 6, d * 4 - 6, d * 4 - 6), fill=255)
    im.putalpha(m.resize((d, d), Image.LANCZOS))
    return im


def glow(d, color):
    y, x = np.mgrid[0:d, 0:d]
    r = np.hypot(x - d / 2, y - d / 2) / (d / 2)
    a = np.clip(1 - r, 0, 1) ** 2.2
    arr = np.zeros((d, d, 4), dtype=np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr)


def make_bg():
    rng = np.random.default_rng(7)
    y = np.linspace(0, 1, H)[:, None]
    base = np.zeros((H, W, 3), dtype=np.float32)
    base[..., 0] = 6 + 10 * y
    base[..., 1] = 8 + 12 * y
    base[..., 2] = 22 + 26 * y
    im = Image.fromarray(base.astype(np.uint8))
    d = ImageDraw.Draw(im)
    for _ in range(420):
        x, yy = int(rng.integers(0, W)), int(rng.integers(0, H))
        b = int(rng.integers(70, 230))
        r = 1 if rng.random() < 0.85 else 2
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=(b, b, min(255, b + 20)))
    return im.filter(ImageFilter.GaussianBlur(0.6)).convert("RGBA")


BG = make_bg()
EARTH = {d: circle_img(AS / "earth.jpg", d) for d in (300, 150, 110, 64)}
MOON = {d: circle_img(AS / "moon.jpg", d, 1.25) for d in (90, 64)}
SUN = {d: circle_img(AS / "sun.jpg", d) for d in (520, 64)}
JUP = {64: circle_img(AS / "jupiter.jpg", 64)}
NEP = {64: circle_img(AS / "neptune.jpg", 64)}
_v = Image.open(AS / "voyager.png").convert("RGBA")
_v = _v.crop(_v.getbbox())
VOY = {w: _v.resize((w, int(_v.height * w / _v.width)), Image.LANCZOS) for w in (860, 420, 300, 64)}
PBD = Image.open(AS / "pale_blue_dot.png").convert("RGB").resize((560, 759), Image.LANCZOS)
GLOW_Y = glow(120, (255, 240, 170))
GLOW_C = glow(90, (140, 230, 255))


class Frame:
    def __init__(self):
        self.im = BG.copy()
        self.ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.ov)

    def paste(self, img, cx, cy, alpha=1.0):
        if alpha <= 0:
            return
        if alpha < 1:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
        self.ov.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))

    def text(self, s, cx, y, size, color=WHITE, alpha=1.0, weight="Black", stroke=6, anchor="ma"):
        if alpha <= 0:
            return
        a = int(255 * clamp(alpha))
        self.d.multiline_text((cx, y), s, font=F(size, weight), fill=color + (a,), anchor=anchor,
                              align="center", spacing=int(size * 0.2),
                              stroke_width=stroke, stroke_fill=(0, 0, 0, a))

    def done(self):
        self.im.alpha_composite(self.ov)
        return self.im.convert("RGB")


def fit(s, size, maxw, weight="Black"):
    while size > 30:
        wd = max(F(size, weight).getlength(p) for p in s.split("\n"))
        if wd <= maxw:
            break
        size -= 2
    return size


def subtitle(fr, t):
    for ln in T["lines"]:
        for s in ln["subs"]:
            if s["start"] <= t < s["end"]:
                txt = s["text"]
                size = fit(txt, 68, 800)
                n = txt.count("\n") + 1
                a = clamp((t - s["start"]) / 0.08 + 0.4)
                y = SUB_Y - (n - 1) * size * 0.6
                bb = fr.d.multiline_textbbox((CX, y), txt, font=F(size), anchor="ma", align="center",
                                             spacing=int(size * 0.2), stroke_width=8)
                fr.d.rounded_rectangle((bb[0] - 26, bb[1] - 14, bb[2] + 26, bb[3] + 18), 22,
                                       fill=(0, 0, 0, int(150 * a)))
                fr.text(txt, CX, y, size, WHITE, a, stroke=8)
                return


def credit(fr):
    fr.text("画像：NASA ／ 音声：VOICEVOX:青山龍星", 60, 1500, 24, GRAY, 0.85, "Medium", 3, "la")


def fmt_hms(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    if h:
        return f"{h}時間{m:02d}分"
    if m:
        return f"{m}分{s:02d}秒"
    return f"{s}秒"


# ---------- 場面 ----------
def sc_hook(fr, t):
    s = L["hook"]
    u = t - s["start"]
    fr.text("光の速さでも", CX, 170, 84, WHITE, 1)
    fr.text("“まる1日”かかる場所", CX, 280, 92, YEL, 1)
    drift = u * 9
    fr.paste(VOY[860], 500 + drift, 800 - drift * 0.6, 1)
    a = ramp(t, sub_start("hook", 2), 0.3)
    if a > 0:
        fr.d.rounded_rectangle((CX - 300, 1080, CX + 300, 1200), 28, fill=(255, 214, 64, int(235 * a)))
        fr.text("2026.11.18", CX, 1086, 88, (10, 14, 30), a, stroke=0)


def sc_moon(fr, t):
    s = L["moon"]
    a0 = ramp(t, s["start"], 0.3)
    fr.text("光の速さ", CX, 160, 60, GRAY, a0, "Bold")
    fr.text("秒速 約30万km", CX, 235, 96, YEL, a0)
    a1 = ramp(t, sub_start("moon", 1), 0.3)
    fr.text("＝ 1秒で地球を7周半", CX, 365, 58, WHITE, a1, "Bold")
    ex, mx, y = 210, 820, 800
    fr.paste(EARTH[300], ex, y, a0)
    am = ramp(t, sub_start("moon", 2) - 0.2, 0.3)
    fr.paste(MOON[90], mx, y, am)
    fr.text("地球", ex, y + 170, 44, WHITE, a0, "Bold", 4)
    fr.text("月", mx, y + 70, 44, WHITE, am, "Bold", 4)
    if am > 0:
        x0, x1 = ex + 150, mx - 45
        for x in range(x0, x1, 22):
            fr.d.line((x, y, x + 10, y), fill=(255, 255, 255, int(90 * am)), width=3)
        t0 = sub_start("moon", 2)
        period, travel = 1.9, 1.28
        ph = (t - t0) % period
        p = clamp(ph / travel)
        if t >= t0:
            px = x0 + (x1 - x0) * p
            for k in range(1, 9):
                tx = px - k * 16
                if tx > x0:
                    fr.paste(GLOW_Y, tx, y, 0.35 * (1 - k / 9) * (1 if p < 1 else 0))
            fr.paste(GLOW_Y, px, y, 1)
            fr.text(f"{min(ph, travel):.2f} 秒", (x0 + x1) / 2, y - 150, 84, YEL, 1)
            fr.text("↑ 実際の速さで動かしています", (x0 + x1) / 2 + 40, y + 150, 36, CYAN, am, "Bold", 4)
        fr.text("38万km", (x0 + x1) / 2, y - 250, 46, GRAY, am, "Bold", 4)
    fr.text("※ 大きさと距離の比は実際と異なります", CX, 1130, 28, GRAY, am * 0.9, "Medium", 3)


def sc_sun(fr, t):
    s = L["sun"]
    a = ramp(t, s["start"], 0.3)
    fr.paste(SUN[520], CX, 520, a)
    fr.text("太陽", CX, 150, 60, WHITE, a, "Bold", 5)
    ey = 1090
    fr.paste(EARTH[110], CX, ey, a)
    fr.text("地球", CX + 120, ey - 30, 44, WHITE, a, "Bold", 4, "la")
    y0, y1 = 790, ey - 62
    p = clamp((t - s["start"]) / (sub_start("sun", 1) + 0.45 - s["start"]))   # 「8分19秒」と言うころに着く
    for yy in range(y0, y1, 22):
        fr.d.line((CX, yy, CX, yy + 10), fill=(255, 255, 255, int(90 * a)), width=3)
    fr.paste(GLOW_Y, CX, y0 + (y1 - y0) * p, a)
    fr.text(fmt_hms(499 * p), 250, 880, 86, YEL, a)
    fr.text("1億5000万km", 770, 900, 44, GRAY, a, "Bold", 4)


ROWS = [  # 名前, 秒, 表示, 画像
    ("地球 → 月", 1.28, "1.3秒", MOON[64]),
    ("太陽 → 地球", 499, "8分19秒", EARTH[64]),
    ("太陽 → 木星", 2597, "43分", JUP[64]),
    ("太陽 → 海王星", 15060, "約4時間11分", NEP[64]),
    ("地球 → ボイジャー1号", 86400, "24時間", VOY[64]),
]
BAR_X0, BAR_X1 = 70, 900


def bars(fr, t, y0, scale_max, shown, alpha=1.0, pitch=150):
    """光でかかる時間を同じ目盛りの棒にする。shown[i] は各行の出方 0〜1。"""
    for i, (name, sec, label, icon) in enumerate(ROWS):
        a = shown[i] * alpha
        if a <= 0:
            continue
        y = y0 + i * pitch
        fr.paste(icon, BAR_X0 + 32, y + 22, a)
        fr.text(name, BAR_X0 + 78, y - 8, 40, WHITE, a, "Bold", 4, "la")
        wd = max(4, (BAR_X1 - BAR_X0) * min(1.0, sec / scale_max) * ease(shown[i]))
        col = YEL if i == 4 else CYAN
        fr.d.rounded_rectangle((BAR_X0, y + 62, BAR_X1, y + 96), 8, fill=(255, 255, 255, int(26 * a)))
        fr.d.rounded_rectangle((BAR_X0, y + 62, BAR_X0 + wd, y + 96), 8, fill=col + (int(255 * a),))
        fr.text(label, BAR_X1, y - 14, 48, col, a, "Black", 5, "ra")


def sc_planets(fr, t):
    s = L["planets"]
    a = ramp(t, s["start"], 0.3)
    fr.text("光でかかる時間", CX, 170, 80, WHITE, a)
    fr.text("同じ目盛りでくらべると", CX, 285, 50, GRAY, a, "Bold", 4)
    sh = [ramp(t, s["start"] + 0.1, 0.4), ramp(t, s["start"] + 0.3, 0.4),
          ramp(t, s["start"] + 0.9, 0.5), ramp(t, sub_start("planets", 1) + 0.6, 0.6), 0]
    bars(fr, t, 440, 15060, sh)


def sc_voyager(fr, t):
    s = L["voyager"]
    u0 = sub_start("voyager", 4)          # 「光でも」から棒グラフに戻る
    a_img = 1 - ramp(t, u0 - 0.3, 0.3)
    if a_img > 0:
        a = ramp(t, s["start"], 0.3) * a_img
        drift = (t - s["start"]) * 6
        fr.paste(VOY[860], 480 + drift, 760 - drift * 0.5, a)
        fr.text("ボイジャー1号", CX, 160, 92, YEL, a)
        a1 = ramp(t, sub_start("voyager", 1), 0.3) * a_img
        fr.text("1977年 打ち上げ", CX, 290, 60, WHITE, a1, "Bold", 5)
        a2 = ramp(t, sub_start("voyager", 2), 0.3) * a_img
        fr.text("49年", 250, 1040, 120, WHITE, a2)
        a3 = ramp(t, sub_start("voyager", 3), 0.3) * a_img
        fr.text("259億km", 690, 1050, 104, YEL, a3)
    b = ramp(t, u0, 0.35)
    if b > 0:
        fr.text("光でかかる時間", CX, 170, 80, WHITE, b)
        fr.text("同じ目盛りでくらべると", CX, 285, 50, GRAY, b, "Bold", 4)
        k = ramp(t, u0 + 0.3, 1.1)
        scale = 15060 * (86400 / 15060) ** k    # 目盛りを 4 時間 → 24 時間へ広げる
        sh = [1, 1, 1, 1, ramp(t, u0 + 0.3, 1.1)]
        bars(fr, t, 440, scale, sh, b)


def sc_signal(fr, t):
    s = L["signal"]
    a = ramp(t, s["start"], 0.3)
    ex, ey, vx, vy = 190, 1010, 760, 470
    fr.paste(EARTH[150], ex, ey, a)
    fr.paste(VOY[300], vx, vy, a)
    fr.text("地球", ex, ey + 90, 44, WHITE, a, "Bold", 4)
    fr.text("ボイジャー1号", vx - 20, vy + 130, 44, WHITE, a, "Bold", 4)
    x0, y0, x1, y1 = ex + 70, ey - 70, vx - 130, vy + 80
    n = 26
    for i in range(n):
        p = i / (n - 1)
        fr.d.ellipse((x0 + (x1 - x0) * p - 3, y0 + (y1 - y0) * p - 3, x0 + (x1 - x0) * p + 3, y0 + (y1 - y0) * p + 3),
                     fill=(255, 255, 255, int(110 * a)))
    t2 = sub_start("signal", 3)
    if t < t2:
        fr.text("いま届く電波は", CX, 150, 64, WHITE, a, "Bold", 5)
        fr.text("24時間前に出発", CX, 240, 92, YEL, ramp(t, sub_start("signal", 1), 0.3))
        p = ((t - s["start"]) % 2.2) / 2.2
        fr.paste(GLOW_C, x1 + (x0 - x1) * p, y1 + (y0 - y1) * p, a)
    else:
        b = ramp(t, t2, 0.3)
        fr.text("指令 → 返事", CX, 150, 64, WHITE, b, "Bold", 5)
        fr.text("往復 48時間", CX, 240, 92, YEL, ramp(t, sub_start("signal", 4) - 0.5, 0.3))
        p = clamp((t - t2) / (s["end"] - t2 - 0.2)) * 2
        q = p if p <= 1 else 2 - p
        fr.paste(GLOW_Y if p <= 1 else GLOW_C, x0 + (x1 - x0) * q, y0 + (y1 - y0) * q, b)
        fr.text("行き 24時間" if p <= 1 else "帰り 24時間", 330, 620, 50, YEL if p <= 1 else CYAN, b, "Bold", 5)


def sc_star(fr, t):
    s = L["star"]
    a = ramp(t, s["start"], 0.3)
    fr.text("太陽の次に近い恒星まで", CX, 150, 60, WHITE, a, "Bold", 5)
    a1 = ramp(t, sub_start("star", 2) - 0.2, 0.3)
    fr.text("光で 4.25年", CX, 235, 100, YEL, a1)
    y = 640
    x0, x1 = 90, 890
    fr.d.line((x0, y, x1, y), fill=(255, 255, 255, int(200 * a)), width=4)
    fr.paste(EARTH[64], x0, y, a)
    fr.paste(glow(110, (255, 170, 120)), x1, y, a)
    fr.text("地球", x0, y + 48, 38, WHITE, a, "Bold", 4)
    fr.text("プロキシマ・\nケンタウリ", x1 - 60, y + 48, 38, WHITE, a, "Bold", 4)
    a2 = ramp(t, sub_start("star", 3), 0.3)
    if a2 > 0:
        # 線の長さ 800px のうち、ボイジャーまでは 800/1552 ≒ 0.5px
        fr.d.line((x0 + 34, y + 110, 330, 880), fill=YEL + (int(255 * a2),), width=3)
        fr.d.line((x0 + 34, y - 6, x0 + 34, y + 110), fill=YEL + (int(255 * a2),), width=3)
        fr.d.rounded_rectangle((110, 880, 890, 1150), 24, fill=(10, 16, 36, int(235 * a2)),
                               outline=YEL + (int(255 * a2),), width=4)
        fr.paste(VOY[64], 180, 950, a2)
        fr.text("ボイジャー1号はここ", 230, 915, 52, YEL, a2, "Black", 4, "la")
        fr.text("この線の 約1/1500\n（画面では0.5ピクセル）", 500, 1000, 44, WHITE, a2, "Bold", 4)


def sc_end(fr, t):
    s = L["end"]
    a = ramp(t, s["start"], 0.4)
    fr.text("49年で、光の“1日ぶん”", CX, 170, 80, YEL, a)
    x, y = CX - 280, 330
    if a > 0:
        fr.d.rounded_rectangle((x - 8, y - 8, x + 568, y + 767), 10, fill=(255, 255, 255, int(200 * a)))
        im = PBD.convert("RGBA")
        fr.paste(im, CX, y + 380, a)
        # 写真の中の地球（小さな点）を丸で示す
        cx, cy = x + int(345 * 560 / 453), y + int(347 * 759 / 614)
        r = 26 + 4 * math.sin(t * 5)
        fr.d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=YEL + (int(255 * a),), width=4)
        fr.text("地球", cx - 90, cy - 30, 40, YEL, a, "Bold", 4)
    fr.text("1990年 ボイジャー1号が撮影した地球", CX, 1115, 36, WHITE, a, "Bold", 4)
    fr.text("NASA/JPL-Caltech", CX, 1165, 28, GRAY, a, "Medium", 3)


SCENES = {"hook": sc_hook, "moon": sc_moon, "sun": sc_sun, "planets": sc_planets,
          "voyager": sc_voyager, "signal": sc_signal, "star": sc_star, "end": sc_end}


def scene_at(t):
    cur = ORDER[0]
    for k in ORDER:
        if t >= L[k]["start"] - 0.1:
            cur = k
    return cur


def draw(t):
    fr = Frame()
    SCENES[scene_at(t)](fr, max(t, L[ORDER[0]]["start"]) if t < L[ORDER[0]]["start"] else t)
    subtitle(fr, t)
    credit(fr)
    im = fr.done()
    # 場面の変わり目と最後を短く暗くする（黒画面にはしない）
    k = 1.0
    for name in ORDER[1:]:
        d = abs(t - (L[name]["start"] - 0.1))
        if d < 0.12:
            k = min(k, 0.45 + 0.55 * d / 0.12)
    if t > TOTAL - 0.35:
        k = min(k, 0.3 + 0.7 * (TOTAL - t) / 0.35)
    if k < 1:
        im = Image.eval(im, lambda v: int(v * k))
    return im


# ---------- 音 ----------
def make_audio():
    with wave.open(str(WORK / "voice.wav")) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    n = len(v)
    tt = np.arange(n) / SR
    rng = np.random.default_rng(3)
    bgm = np.zeros(n, dtype=np.float32)
    # 自作の BGM：ゆっくり揺れる和音（A・E・A・C・E・B）
    for f, g in ((55, .9), (82.41, .6), (110, .7), (130.81, .45), (164.81, .4), (246.94, .22), (329.63, .14)):
        for det in (-0.35, 0.3):
            lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (0.05 + rng.random() * 0.08) * tt + rng.random() * 6)
            bgm += g * lfo * np.sin(2 * np.pi * (f + det) * tt + rng.random() * 6)
    # 場面の変わり目に小さな鐘の音
    for name in ORDER[1:]:
        t0 = L[name]["start"] - 0.1
        i0 = int(t0 * SR)
        m = min(n - i0, int(2.5 * SR))
        x = np.arange(m) / SR
        bgm[i0:i0 + m] += 2.2 * np.exp(-x * 2.2) * (np.sin(2 * np.pi * 880 * x) + 0.5 * np.sin(2 * np.pi * 1318.5 * x))
    bgm /= np.max(np.abs(bgm))
    fade = np.clip(tt / 0.4, 0, 1) * np.clip((n / SR - tt) / 1.0, 0, 1)
    mix = v * 0.9 + bgm * 0.085 * fade
    mix = np.clip(mix / max(1.0, np.max(np.abs(mix))), -1, 1)
    with wave.open(str(WORK / "premix.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    # −14 LUFS にそろえる（2 回がけ）
    flt = "loudnorm=I=-14:TP=-1.5:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(WORK / "premix.wav"), "-af", flt + ":print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    flt2 = (f"{flt}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
            f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(WORK / "premix.wav"),
                    "-af", flt2, "-ar", str(SR), "-ac", "2", str(WORK / "norm.wav")], check=True)
    # ステレオにしたあとの実測で、ずれたぶんだけ音量を足し引きする
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(WORK / "norm.wav"), "-af", "ebur128",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    i_now = float(r.stderr[r.stderr.rindex("I:") + 2:].split("LUFS")[0])
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(WORK / "norm.wav"),
                    "-af", f"volume={-14.0 - i_now:.2f}dB", str(WORK / "mix.wav")], check=True)
    print("mix.wav を書いた")


def render():
    out = WORK / "001.mp4"
    n = int(round(TOTAL * FPS))
    p = subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-i", str(WORK / "mix.wav"),
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(draw(i / FPS).tobytes())
        if i % 150 == 0:
            print(f"{i}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("書き出し完了", out, f"{n} コマ")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "audio":
        make_audio()
    elif cmd == "stills":
        (WORK / "stills").mkdir(exist_ok=True)
        for s in sys.argv[2].split(","):
            draw(float(s)).resize((540, 960), Image.LANCZOS).save(WORK / "stills" / f"t{float(s):05.1f}.png")
    elif cmd == "render":
        render()
