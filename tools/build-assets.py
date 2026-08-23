#!/usr/bin/env python3
"""Build interactive-map assets for Meet Greater South 2026 from the venue map JPG."""
import os, subprocess, json
from PIL import Image, ImageDraw

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PROJ, "data", "map", "(0820更新)地圖.jpg")
OUT = os.path.join(PROJ, "assets")
SCRATCH = os.path.join(PROJ, ".build")

# floor-plan card crop inside the original 5947x3000 poster (0820 update)
CROP = (80, 569, 5105, 2932)          # -> 5025 x 2363, ratio 2.1265
VBW, VBH = CROP[2] - CROP[0], CROP[3] - CROP[1]

# key: (box in ORIGINAL poster px, colour)  — box is the zoom/label anchor
# EXTRA_HITS adds further rectangles for L-shaped areas.
SPOTS = {
    # ---- stages / spaces (schedule) ----
    "sunrise":    ((1235, 680, 1999, 1388), "#E6298F"),
    "fever":      ((4227, 784, 4739, 1192), "#F5B417"),
    "cocreation": ((303, 2108, 747, 2496), "#1E6FD9"),
    "match2":     ((3079, 686, 3643, 989), "#66C6E8"),
    "match1":     ((3659, 684, 3971, 992), "#3FBFB4"),
    # ---- industry theme pavilions ----
    "cx-01": ((899, 2108, 2851, 2448), "#5FBBDA"),
    "cx-02": ((3079, 2108, 4847, 2448), "#5FBBDA"),
    "cx-03": ((3075, 1396, 3435, 1748), "#5FBBDA"),
    "cx-04": ((3075, 1064, 3395, 1248), "#5FBBDA"),
    "cx-05": ((2151, 856, 2851, 1168), "#5FBBDA"),
    "cx-06": ((2151, 1372, 2851, 1960), "#5FBBDA"),
    "cx-07": ((899, 1552, 1367, 1900), "#5FBBDA"),
    "cx-08": ((3883, 1270, 4033, 1460), "#5FBBDA"),
    "ep-01": ((1699, 1552, 1859, 1900), "#7FCCE4"),
    "ep-02": ((1419, 1552, 1651, 1900), "#7FCCE4"),
    "ep-03": ((1019, 1044, 1211, 1384), "#7FCCE4"),
    # ---- pavilions & solution clusters ----
    "gp":  ((336, 1485, 728, 2025), "#A85DA3"),
    "h":   ((1921, 1487, 2056, 1962), "#3BB1B1"),
    "t":   ((295, 860, 683, 1365), "#9C7A56"),
    "sig": ((3505, 1375, 3831, 1720), "#3DB76D"),
    "e":   ((3065, 1799, 4606, 1949), "#EC1E8C"),
    "f":   ((3892, 1528, 4023, 1702), "#1B63C4"),
    "s":   ((4088, 1406, 4219, 1715), "#78C172"),
    "m":   ((4285, 1369, 4650, 1724), "#F5C21F"),
    "g":   ((3761, 1070, 4115, 1192), "#B9D958"),
    "p":   ((3494, 1064, 3658, 1236), "#F0862F"),
}

# extra hit rectangles (original poster px) for areas that are not a single block
EXTRA_HITS = {
    "t": [(166, 915, 260, 1800)],          # the T3-9 … T3-17 column down the left edge
}

# zoom crops need the whole cluster, not just the anchor block
ZOOM_BOX = {
    "t": (166, 855, 693, 1805),
}

LABEL_AT = {"t": [407, 473]}

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
