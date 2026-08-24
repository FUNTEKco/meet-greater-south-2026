#!/usr/bin/env python3
"""Build the 1200x630 OG cards for the three pages (root / stage/ / zone/).

Each card = 品牌底色 + 標題列 + 大會地圖,並把該頁「可點的那一類」熱區描邊發光,
所以貼到 LINE 的預覽圖一眼就看得出是舞台頁還是展區頁。

熱區座標直接讀 index.html 的 polys(viewBox 5025x2363),兩邊不會走鐘。
字型用 macOS 內建的 Heiti TC Medium;產出的 jpg 有進版控,一般不需要重跑。
"""
import os, re
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(PROJ, "index.html")
BASE = os.path.join(PROJ, "assets", "map-base.jpg")
OUT = os.path.join(PROJ, "assets")
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"

VB = (5025, 2363)                     # index.html 的 SVG viewBox
W, H = 1200, 630                      # OG 建議尺寸
PAD = 90                              # 左右留白 = 地圖置中後的邊距
HEAD_H = 150                          # 上方標題列高度

EYEBROW = "MEET GREATER SOUTH · 亞灣新創大南方 · 8/28–8/29"
CARDS = {
    "og-home":  ("2026 互動展區地圖",  "點展區看攤位名錄,點舞台看節目表", None),
    "og-stage": ("舞台節目表",         "5 個舞台與活動空間 · 兩天完整節目", "stage"),
    "og-zone":  ("展區與攤位名錄",     "21 個展區 · 244 家參展單位",       "zone"),
}


def read_spots():
    """index.html 的 STAGES / ZONES -> [(type, color, [polygon points])]"""
    src = open(INDEX, encoding="utf-8").read()
    consts = dict(re.findall(r"(\w+) = '(#[0-9A-Fa-f]{6})'", src))
    spots = []
    for name, kind in (("STAGES", "stage"), ("ZONES", "zone")):
        m = re.search(r"const %s = \[(.*?)\n  \];" % name, src, re.S)
        if not m:
            raise SystemExit(f"index.html 找不到 {name}")
        for obj in re.findall(r"\{(.*?)\}\s*(?:,|$)(?=\s*(?:\{|\Z))", m.group(1), re.S):
            color = re.search(r"color:\s*(?:'(#[0-9A-Fa-f]{6})'|(\w+))", obj)
            polys = re.search(r"polys:\s*\[(.*?)\]", obj, re.S)
            if not (color and polys):
                continue
            hexcol = color.group(1) or consts[color.group(2)]
            pts = [[tuple(map(int, p.split(","))) for p in s.split()]
                   for s in re.findall(r"'([^']+)'", polys.group(1))]
            spots.append((kind, hexcol, pts))
    return spots


def brand_bg():
    """跟 index.html 一樣的深藍漸層,加兩坨青綠光暈(screen 疊加,只會變亮)。"""
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    top, mid, bot = (4, 20, 31), (6, 38, 58), (7, 60, 82)
    for y in range(H):
        t = y / (H - 1)
        a, b, u = (top, mid, t / 0.54) if t < 0.54 else (mid, bot, (t - 0.54) / 0.46)
        d.line([(0, y), (W, y)], fill=tuple(round(a[i] + (b[i] - a[i]) * u) for i in range(3)))

    glow = Image.new("RGB", (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse([-260, -320, 660, 400], fill=(0, 105, 128))
    g.ellipse([760, -300, 1560, 320], fill=(9, 96, 80))
    return ImageChops.screen(bg, glow.filter(ImageFilter.GaussianBlur(190)))


def map_layer(highlight):
    """地圖 + 指定分類的熱區描邊發光,回傳已縮放好的圖。"""
    src = Image.open(BASE).convert("RGB")
    sx, sy = src.width / VB[0], src.height / VB[1]

    glow = Image.new("RGBA", src.size, (0, 0, 0, 0))
    fill = Image.new("RGBA", src.size, (0, 0, 0, 0))
    gd, fd = ImageDraw.Draw(glow), ImageDraw.Draw(fill)
    for kind, hexcol, polys in read_spots():
        if highlight and kind != highlight:
            continue
        c = tuple(int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
        for pts in polys:
            xy = [(x * sx, y * sy) for x, y in pts]
            gd.polygon(xy, outline=c + (255,), width=7)
            fd.polygon(xy, fill=c + (56,), outline=c + (235,), width=3)
    src = Image.alpha_composite(src.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(9)))
    src = Image.alpha_composite(src, fill).convert("RGB")

    h = H - HEAD_H - 34
    return src.resize((round(h * src.width / src.height), h), Image.LANCZOS)


def spaced(draw, xy, text, font, fill, tracking=0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


def build(name, title, sub, highlight):
    card = brand_bg()
    m = map_layer(highlight)
    card.paste(m, ((W - m.width) // 2, HEAD_H + 4))

    d = ImageDraw.Draw(card)
    f_eye = ImageFont.truetype(FONT, 17, index=0)
    f_title = ImageFont.truetype(FONT, 54, index=0)
    f_sub = ImageFont.truetype(FONT, 22, index=0)

    spaced(d, (PAD, 34), EYEBROW, f_eye, (125, 205, 230), tracking=1.4)
    d.text((PAD, 62), title, font=f_title, fill=(242, 251, 255))
    d.text((PAD + d.textlength(title, font=f_title) + 18, 84), sub, font=f_sub, fill=(140, 190, 212))
    d.line([(PAD, 137), (W - PAD, 137)], fill=(30, 78, 100), width=1)

    path = os.path.join(OUT, name + ".jpg")
    card.save(path, "JPEG", quality=88, optimize=True, progressive=True)
    print(f"wrote {os.path.relpath(path, PROJ)}  {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    for name, (title, sub, highlight) in CARDS.items():
        build(name, title, sub, highlight)
