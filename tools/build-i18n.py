#!/usr/bin/env python3
"""Assemble the Japanese dictionary i18n/ja.js from data/i18n/ja/*.json.

  data/i18n/ja/ui.json            — 介面字串、VIEWS、舞台/展區名稱與介紹、節目名稱
  data/i18n/ja/booths/<key>.json  — 各展區的攤商介紹日譯(key = index.html 的 spot key)

index.html 只在 ?lang=ja 時載入 i18n/ja.js,並以「展區 key + 中文顯示名稱」對回
BOOTHS;對不到的攤商會維持中文,所以名錄換版後只要重跑本腳本看缺漏清單再補譯即可。

    python3 tools/build-i18n.py
"""
import os, json, glob, re

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PROJ, "data", "i18n", "ja")
INDEX = os.path.join(PROJ, "index.html")
OUT = os.path.join(PROJ, "i18n", "ja.js")


def load_booths_zh():
    """index.html 內 BOOTHS 區塊 → {spot key: [[code, name, desc], ...]}"""
    html = open(INDEX, encoding="utf-8").read()
    m = re.search(r"const BOOTHS = \{\n(.*?)\n  \};\n  // ---------- /BOOTHS", html, re.S)
    if not m:
        raise SystemExit("index.html 找不到 BOOTHS 標記區塊")
    booths = {}
    for line in m.group(1).split("\n"):
        key, _, val = line.strip().partition(": ")
        booths[json.loads(key)] = json.loads(val.rstrip(",").replace("<\\/", "</"))
    return booths


def main():
    ui = json.load(open(os.path.join(SRC, "ui.json"), encoding="utf-8"))
    zh = load_booths_zh()

    booths, n_ok, missing, extra = {}, 0, [], []
    for key, lst in zh.items():
        path = os.path.join(SRC, "booths", f"{key}.json")
        items = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
        ja = {}
        for it in items:
            ja[it["zh"]] = [it.get("ja") or "", it.get("desc") or ""]
        names = {name for _, name, _ in lst}
        for name in ja:
            if name not in names:
                extra.append(f"{key}: {name!r}")
        for code, name, desc in lst:
            if name in ja and (ja[name][1] or not desc):
                n_ok += 1
            else:
                missing.append(f"{key} {code} {name}")
        booths[key] = ja

    data = {
        "ui": ui["ui"],
        "stages": ui["stages"],
        "zones": ui["zones"],
        "schedule": ui["schedule"],
        "booths": booths,
    }
    body = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("// 由 tools/build-i18n.py 產生 — 請改 data/i18n/ja/*.json 再重跑,不要直接編輯本檔。\n")
        f.write("window.I18N_JA = " + body + ";\n")

    total = sum(len(v) for v in zh.values())
    print(f"wrote i18n/ja.js: {len(ui['zones'])} zones, {len(ui['schedule'])} sessions, "
          f"booths {n_ok}/{total} translated")
    if missing:
        print(f"\n尚未翻譯的攤商({len(missing)}),頁面上會維持中文:")
        for m in missing:
            print("  -", m)
    if extra:
        print(f"\n譯文找不到對應攤商({len(extra)}),可能是名錄換版後名稱改了:")
        for e in extra:
            print("  -", e)


if __name__ == "__main__":
    main()
