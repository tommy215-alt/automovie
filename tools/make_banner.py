from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, numpy as np
W, H = 2560, 1440
def F(size, w="Black"):
    f = ImageFont.truetype("C:/Windows/Fonts/NotoSansJP-VF.ttf", size); f.set_variation_by_name(w); return f
YEL = (255, 200, 40)
# 背景：紺のグラデーション（中央が少し明るい）
y, x = np.mgrid[0:H, 0:W]
r = np.hypot((x - W/2) / (W/2), (y - H/2) / (H/2))
k = np.clip(1 - r, 0, 1)
bg = np.stack([12 + 22*k, 18 + 30*k, 40 + 56*k], axis=-1).astype(np.uint8)
im = Image.fromarray(bg)
d = ImageDraw.Draw(im)
rng = np.random.default_rng(5)
for _ in range(500):                                   # 星
    sx, sy = int(rng.integers(0, W)), int(rng.integers(0, H)); b = int(rng.integers(60, 190)); rr = 1 if rng.random() < .8 else 2
    d.ellipse((sx-rr, sy-rr, sx+rr, sy+rr), fill=(b, b, min(255, b+25)))
# 大きなうすい輪（テレビ表示で上下に見える飾り）
for cx, cy, R, wd, a0, a1 in ((W/2, H/2, 930, 22, -90, 200),):
    d.ellipse((cx-R, cy-R, cx+R, cy+R), outline=(40, 52, 86), width=wd)
    d.arc((cx-R, cy-R, cx+R, cy+R), start=a0, end=a1, fill=(120, 98, 30), width=wd)
# 安全な範囲（中央 1546×423）の中に、マークと名前
cy = H/2
R, wd = 150, 30
tag = "実際にあった世界の出来事を、60秒で　｜　毎日18時更新"
w1, w2, w3 = d.textlength("世界の", font=F(170)), d.textlength("60", font=F(190)), d.textlength("秒", font=F(170))
tw = w1 + 10 + w2 + 10 + w3
total = 2*R + 70 + tw
ix = W/2 - total/2 + R                                   # マークと名前を、まとめて中央に置く
d.ellipse((ix-R, cy-R, ix+R, cy+R), outline=(70, 84, 122), width=wd)
d.arc((ix-R, cy-R, ix+R, cy+R), start=-90, end=200, fill=YEL, width=wd)
for a in (-90, 200):
    px, py = ix + (R - wd/2) * math.cos(math.radians(a)), cy + (R - wd/2) * math.sin(math.radians(a))
    d.ellipse((px - wd/2, py - wd/2, px + wd/2, py + wd/2), fill=YEL)
d.text((ix, cy - 6), "60", font=F(150), fill=(255, 255, 255), anchor="mm")
tx = ix + R + 70
d.text((tx, cy - 50), "世界の", font=F(170), fill=(255, 255, 255), anchor="lm")
d.text((tx + w1 + 10, cy - 50), "60", font=F(190), fill=YEL, anchor="lm")
d.text((tx + w1 + w2 + 20, cy - 50), "秒", font=F(170), fill=(255, 255, 255), anchor="lm")
size = 46
while d.textlength(tag, font=F(size, "Bold")) > tw:
    size -= 1
d.text((tx + 4, cy + 105), tag, font=F(size, "Bold"), fill=(200, 210, 230), anchor="lm")
assert total < 1546 - 60, total
im.save("channel/banner.png")
# 見え方の確認：全体（テレビ）と、中央 1546×423（スマホ・PC の最小）
pv = Image.new("RGB", (1300, 1010), (255, 255, 255))
full = im.resize((1280, 720)); fd = ImageDraw.Draw(full)
fd.rectangle(((2560-1546)/2/2, (1440-423)/2/2, (2560+1546)/2/2, (1440+423)/2/2), outline=(255, 60, 60), width=2)
pv.paste(full, (10, 10))
pv.paste(im.crop(((W-1546)//2, (H-423)//2, (W+1546)//2, (H+423)//2)).resize((1280, 350)), (10, 745))
pv.save("channel/banner_preview.png")
print(im.size, round(__import__("os").path.getsize("channel/banner.png")/1e6, 2), "MB")
