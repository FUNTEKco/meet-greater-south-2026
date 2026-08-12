#!/usr/bin/env python3
"""Build interactive-map assets for Meet Greater South 2026 from the venue map JPG."""
import os, subprocess, json
from PIL import Image, ImageDraw

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PROJ, "map", "Meet 大南方地圖.jpg")
OUT = os.path.join(PROJ, "assets")
SCRATCH = os.path.join(PROJ, ".build")

# floor-plan card crop inside the original 6011x3000 poster
CROP = (84, 512, 5130, 2874)          # -> 5046 x 2362, ratio 2.1363
VBW, VBH = CROP[2] - CROP[0], CROP[3] - CROP[1]

# key: (box in ORIGINAL poster px, colour)  — box is the zoom/label anchor
# EXTRA_HITS adds further rectangles for L-shaped areas.
SPOTS = {
    # ---- stages / spaces (schedule) ----
    "sunrise":    ((1252, 620, 2016, 1328), "#E6298F"),
    "fever":      ((4244, 724, 4756, 1132), "#F5B417"),
    "cocreation": ((320, 2048, 764, 2436), "#1E6FD9"),
    "match2":     ((3096, 626, 3660, 929), "#66C6E8"),
    "match1":     ((3676, 624, 3988, 932), "#3FBFB4"),
    # ---- industry theme pavilions ----
    "cx-01": ((916, 2048, 2868, 2388), "#5FBBDA"),
    "cx-02": ((3096, 2048, 4864, 2388), "#5FBBDA"),
    "cx-03": ((3092, 1336, 3452, 1688), "#5FBBDA"),
    "cx-04": ((3092, 1004, 3412, 1188), "#5FBBDA"),
    "cx-05": ((2168, 796, 2868, 1108), "#5FBBDA"),
    "cx-06": ((2168, 1312, 2868, 1900), "#5FBBDA"),
    "cx-07": ((916, 1492, 1384, 1840), "#5FBBDA"),
    "cx-08": ((3900, 1210, 4050, 1400), "#5FBBDA"),
    "ep-01": ((1716, 1492, 1876, 1840), "#7FCCE4"),
    "ep-02": ((1436, 1492, 1668, 1840), "#7FCCE4"),
    "ep-03": ((1036, 984, 1228, 1324), "#7FCCE4"),
    # ---- pavilions & solution clusters ----
    "gp":  ((353, 1425, 745, 1965), "#A85DA3"),
    "h":   ((1938, 1427, 2073, 1902), "#3BB1B1"),
    "t":   ((312, 800, 700, 1305), "#9C7A56"),
    "sig": ((3522, 1315, 3848, 1660), "#3DB76D"),
    "e":   ((3082, 1739, 4623, 1889), "#EC1E8C"),
    "f":   ((3909, 1468, 4040, 1642), "#1B63C4"),
    "s":   ((4105, 1346, 4236, 1655), "#78C172"),
    "m":   ((4302, 1309, 4667, 1664), "#F5C21F"),
    "g":   ((3778, 1010, 4132, 1132), "#B9D958"),
    "p":   ((3511, 1004, 3675, 1176), "#F0862F"),
}

# extra hit rectangles (original poster px) for areas that are not a single block
EXTRA_HITS = {
    "t": [(183, 855, 277, 1740)],          # the T3-9 … T3-17 column down the left edge
}

# zoom crops need the whole cluster, not just the anchor block
ZOOM_BOX = {
    "t": (183, 795, 710, 1745),
}

LABEL_AT = {"t": [420, 470]}

MIN_HIT = 180  # minimum hotspot side in viewBox px, so small booths stay tappable


def to_vb(box):
    """original-poster px -> viewBox px, with a minimum tappable size."""
    x0, y0, x1, y1 = box
    x0 -= CROP[0]; x1 -= CROP[0]; y0 -= CROP[1]; y1 -= CROP[1]
    if x1 - x0 < MIN_HIT:
        c = (x0 + x1) / 2; x0, x1 = c - MIN_HIT / 2, c + MIN_HIT / 2
    if y1 - y0 < MIN_HIT:
        c = (y0 + y1) / 2; y0, y1 = c - MIN_HIT / 2, c + MIN_HIT / 2
    x0 = max(0, min(VBW, x0)); x1 = max(0, min(VBW, x1))
    y0 = max(0, min(VBH, y0)); y1 = max(0, min(VBH, y1))
    return [round(v) for v in (x0, y0, x1, y1)]


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    im = Image.open(SRC).convert("RGB")
    base = im.crop(CROP)
    print("base", base.size, round(base.width / base.height, 4))

    # ---- base map: webp (2x) + jpg fallback ----
    big = base.resize((2600, round(2600 * base.height / base.width)), Image.LANCZOS)
    big.save(os.path.join(OUT, "map-base.png"))
    subprocess.run(["cwebp", "-q", "84", "-quiet", os.path.join(OUT, "map-base.png"),
                    "-o", os.path.join(OUT, "map-base.webp")], check=True)
    os.remove(os.path.join(OUT, "map-base.png"))
    base.resize((1800, round(1800 * base.height / base.width)), Image.LANCZOS)\
        .save(os.path.join(OUT, "map-base.jpg"), quality=82, optimize=True, progressive=True)

    # ---- per-zone zoom crops ----
    meta = {}
    for key, (anchor, colour) in SPOTS.items():
        box = ZOOM_BOX.get(key, anchor)
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        padx = max(w * 0.30, 340); pady = max(h * 0.30, 260)
        # keep a readable minimum window
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        cw = max(w + 2 * padx, 1500); ch = max(h + 2 * pady, 900)
        cw = max(cw, ch * 1.5); ch = max(ch, cw / 2.2)
        cx0, cy0 = cx - cw / 2, cy - ch / 2
        cx1, cy1 = cx + cw / 2, cy + ch / 2
        # clamp into the floor-plan card
        if cx0 < CROP[0]: cx1 += CROP[0] - cx0; cx0 = CROP[0]
        if cx1 > CROP[2]: cx0 -= cx1 - CROP[2]; cx1 = CROP[2]
        if cy0 < CROP[1]: cy1 += CROP[1] - cy0; cy0 = CROP[1]
        if cy1 > CROP[3]: cy0 -= cy1 - CROP[3]; cy1 = CROP[3]
        cx0 = max(CROP[0], cx0); cy0 = max(CROP[1], cy0)
        cx1 = min(CROP[2], cx1); cy1 = min(CROP[3], cy1)
        crop = im.crop((round(cx0), round(cy0), round(cx1), round(cy1)))

        # subtle highlight ring around the zone itself
        ov = crop.convert("RGBA")
        d = ImageDraw.Draw(ov, "RGBA")
        rgb = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
        for rx0, ry0, rx1, ry1 in [anchor] + EXTRA_HITS.get(key, []):
            d.rounded_rectangle([rx0 - cx0, ry0 - cy0, rx1 - cx0, ry1 - cy0], radius=18,
                                outline=rgb + (255,), width=9)
        crop = ov.convert("RGB")

        tw = 1100
        crop = crop.resize((tw, round(tw * crop.height / crop.width)), Image.LANCZOS)
        png = os.path.join(SCRATCH, f"z_{key}.png")
        crop.save(png)
        subprocess.run(["cwebp", "-q", "80", "-quiet", png,
                        "-o", os.path.join(OUT, f"zone-{key}.webp")], check=True)
        os.remove(png)
        rects = [to_vb(r) for r in [anchor] + EXTRA_HITS.get(key, [])]
        meta[key] = {
            "polys": [f"{a},{b} {c},{b} {c},{d2} {a},{d2}" for a, b, c, d2 in rects],
            "label": LABEL_AT.get(key) or [
                round((rects[0][0] + rects[0][2]) / 2), round((rects[0][1] + rects[0][3]) / 2)],
        }

    with open(os.path.join(SCRATCH, "spots.json"), "w") as f:
        json.dump({"vb": [VBW, VBH], "spots": meta}, f, indent=1)
    for k, v in meta.items():
        print(f'{k:11s} polys={v["polys"]} label={v["label"]}')

    # ---- verification overlay ----
    ver = base.convert("RGBA")
    d = ImageDraw.Draw(ver, "RGBA")
    fnt = None
    try:
        from PIL import ImageFont
        fnt = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 46)
    except Exception:
        pass
    for key, (anchor, colour) in SPOTS.items():
        rgb = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
        for x0, y0, x1, y1 in [to_vb(r) for r in [anchor] + EXTRA_HITS.get(key, [])]:
            d.rectangle([x0, y0, x1, y1], outline=rgb + (255,), width=12)
            d.rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], fill=rgb + (34,))
            d.text((x0 + 16, y0 + 10), key, fill=(0, 0, 0), font=fnt,
                   stroke_width=5, stroke_fill=(255, 255, 255))
    ver = ver.convert("RGB")
    ver.resize((1800, round(1800 * ver.height / ver.width)), Image.LANCZOS)\
       .save(os.path.join(SCRATCH, "verify.png"))
    print("wrote verify.png")


if __name__ == "__main__":
    main()
