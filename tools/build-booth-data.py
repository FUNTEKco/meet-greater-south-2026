#!/usr/bin/env python3
"""Rebuild both booth data outputs from data/booth-raw/*.csv — the single source of truth.

  1. data/booth/NN_<展區>.txt   — PinChat AI 訓練用名錄(每個展區一個檔 + 00 總覽)
  2. index.html 的 BOOTHS 區塊   — 地圖下方的攤位按鈕與攤商介紹

Run after the organiser sends an updated 參展商資料 export:
    python3 tools/build-booth-data.py
"""
import os, csv, json, glob, re

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(PROJ, "data", "booth-raw")
OUT = os.path.join(PROJ, "data", "booth")
INDEX = os.path.join(PROJ, "index.html")

EVENT = "2026 Meet 大南方"

# CSV 檔 -> 參展類別
CATEGORY = {
    "Meet 大南方參展商資料 - 參展商.csv": "國內參展商",
    "Meet 大南方參展商資料 - 國際參展商.csv": "國際參展商",
    "Meet 大南方參展商資料 - 市集團隊.csv": "市集團隊",
}

# CSV 展區名 -> (檔案序號, 檔名用展區名, index.html 的 spot key)
# 檔案序號 01–14 沿用既有檔案,15– 為 0820 更新後新增的展區。
ZONES = {
    "智慧製造與產線升級":           (1,  "智慧製造與產線升級",           "s"),
    "淨零碳排與綠能永續":           (2,  "淨零碳排與綠能永續",           "g"),
    "品牌轉型與跨境行銷":           (3,  "品牌轉型與跨境行銷",           "m"),
    "醫療健康與高齡照護":           (4,  "醫療健康與高齡照護",           "h"),
    "數位管理與企業效率":           (5,  "數位管理與企業效率",           "e"),
    "未來零售與餐飲科技":           (6,  "未來零售與餐飲科技",           "f"),
    "生態系夥伴":                   (7,  "生態系夥伴",                   "p"),
    "南臺灣科研產業化平台":         (8,  "南臺灣科研產業化平台",         "sig"),
    "TAA臺灣科技新創基地":          (9,  "TAA臺灣科技新創基地",          "cx-07"),
    "中華電信5G加速器專區":         (10, "中華電信5G加速器專區",         "ep-02"),
    "經濟部產業發展署主題館":       (11, "經濟部產業發展署主題館",       "cx-01"),
    "經濟部中小及新創企業署主題館": (12, "經濟部中小及新創企業署主題館", "cx-05"),
    "高雄市政府主題專區":           (13, "高雄市政府主題專區",           "cx-06"),
    "國際館":                       (14, "國際館",                       "gp"),
    "經濟部產業技術司主題專區":     (15, "經濟部產業技術司主題專區",     "cx-02"),
    "文化內容策進院主題專區":       (16, "文化內容策進院主題專區",       "cx-03"),
    "櫃買中心創櫃新星主題專區":     (17, "櫃買中心創櫃新星主題專區",     "cx-04"),
    "CCIA x CCBI 跨境創新專館":     (18, "CCIA x CCBI跨境創新專館",      "ep-01"),
    "極智移動 Lean Mobility":       (19, "極智移動 Lean Mobility",       "ep-03"),
    "風土餐桌市集":                 (20, "風土餐桌市集",                 "t"),
}

# 地圖上有標示、但主辦單位未提供參展商名錄的展位
NO_ROSTER = "CX-08 中華民國全國中小企業總會（單一單位展位，主辦單位未提供參展商名錄）"

SEP = "=" * 60


def read_rows():
    rows = []
    for path in sorted(glob.glob(os.path.join(RAW, "*.csv"))):
        cat = CATEGORY.get(os.path.basename(path))
        if cat is None:
            raise SystemExit(f"未知的來源檔,請先在 CATEGORY 補上分類:{path}")
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                r = {k: (v or "").strip() for k, v in r.items() if k}
                if not r.get("公司名稱"):
                    continue
                if r["展區"] not in ZONES:
                    raise SystemExit(f"未知的展區名,請先在 ZONES 補上對照:「{r['展區']}」({path})")
                r["參展類別"] = cat
                rows.append(r)
    return rows


def main():
    rows = read_rows()
    by_zone = {}
    for r in rows:
        by_zone.setdefault(r["展區"], []).append(r)

    n_zone = len(by_zone)
    n_all = len(rows)
    by_cat = {}
    for r in rows:
        by_cat[r["參展類別"]] = by_cat.get(r["參展類別"], 0) + 1
    breakdown = "、".join(f"{k} {v} 家" for k, v in
                          sorted(by_cat.items(), key=lambda kv: -kv[1]))
    scope = f"本活動共 {n_zone} 個展區、{n_all} 家參展單位"

    order = sorted(by_zone, key=lambda z: ZONES[z][0])

    # ---------- 1. 各展區 txt ----------
    for fname in glob.glob(os.path.join(OUT, "*.txt")):
        os.remove(fname)

    for zone in order:
        num, fname, _ = ZONES[zone]
        items = by_zone[zone]
        n = len(items)
        out = [
            f"文件名稱：{EVENT}｜{zone} 展區參展商名錄",
            f"活動名稱：{EVENT}",
            f"展區名稱：{zone}",
            f"參展商家數：{n} 家（{scope}）",
            "本文件內容：此展區所有參展商的公司名稱、攤位編號、產品與服務介紹。",
            "", SEP, "",
            f"[展區索引] {EVENT}｜{zone}",
            f"「{zone}」展區共有 {n} 家參展商，攤位編號與公司名稱如下：",
        ]
        for r in items:
            out.append(f"- {r['攤位編號']}｜{r['公司名稱']}")
        for i, r in enumerate(items, 1):
            out += [
                "", SEP, "",
                f"[參展商 {i:02d}/{n}] {r['公司名稱']}（{zone}）",
                f"公司名稱：{r['公司名稱']}",
                f"展區：{zone}",
                f"攤位編號：{r['攤位編號']}",
                f"參展類別：{r['參展類別']}",
                f"活動名稱：{EVENT}",
                f"摘要：{r['公司名稱']} 參加 {EVENT}，設攤於「{zone}」展區，"
                f"攤位編號 {r['攤位編號']}。",
                "產品與服務介紹：",
                r["產品服務"].strip(),
            ]
        path = os.path.join(OUT, f"{num:02d}_{fname}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        print(f"wrote {os.path.basename(path):44s} {n:3d} 家")

    # ---------- 2. 00_展區總覽 ----------
    ov = [
        f"文件名稱：{EVENT} 展區總覽與檔案索引",
        f"{EVENT} 共設 {n_zone} 個展區、{n_all} 家參展單位（{breakdown}）。",
        "各展區與參展商家數如下：",
    ]
    for zone in order:
        num, fname, _ = ZONES[zone]
        ov.append(f"- {zone}：{len(by_zone[zone])} 家"
                  f"（詳細名錄見檔案 {num:02d}_{fname}.txt）")
    ov += [
        "",
        f"以上 {n_zone} 個展區家數加總 = {n_all} 家，"
        f"即本活動參展單位總數（{breakdown}）。",
        f"另註：{NO_ROSTER}，不計入上述家數。",
    ]
    with open(os.path.join(OUT, "00_展區總覽.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(ov) + "\n")
    print(f"wrote {'00_展區總覽.txt':44s} {n_zone} 展區 / {n_all} 家")

    # ---------- 3. index.html 的 BOOTHS ----------
    booths = {}
    for zone in order:
        key = ZONES[zone][2]
        booths[key] = [[r["攤位編號"], r["公司名稱"], r["產品服務"].strip()]
                       for r in by_zone[zone]]

    lines = ["  const BOOTHS = {"]
    for key in booths:
        lines.append(f"    {json.dumps(key, ensure_ascii=False)}: " +
                     json.dumps(booths[key], ensure_ascii=False) + ",")
    lines.append("  };")
    block = "\n".join(lines).replace("</", "<\\/")

    html = open(INDEX, encoding="utf-8").read()
    start = "  // ---------- BOOTHS: generated by tools/build-booth-data.py ----------\n"
    end = "\n  // ---------- /BOOTHS ----------"
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pat.search(html):
        raise SystemExit("index.html 找不到 BOOTHS 標記區塊")
    html = pat.sub(lambda _: start + block + end, html, count=1)
    open(INDEX, "w", encoding="utf-8").write(html)
    print(f"patched index.html BOOTHS: {len(booths)} zones, {n_all} booths, "
          f"{len(block)/1024:.0f} KB")


if __name__ == "__main__":
    main()
