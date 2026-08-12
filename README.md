# 2026 Meet Greater South 亞灣新創大南方 — 互動展區地圖

**線上版:https://funtekco.github.io/meet-greater-south-2026/**

比照 `ai-taiwan-2026` 的做法,把大會地圖與舞台節目總表做成一頁式互動地圖。
單一檔案 `index.html`(無框架、無外部相依),搭配 `assets/` 內的圖片即可部署。

推送到 `main` 後由 GitHub Pages 自動發佈(來源:`main` 分支根目錄)。

## 內容來源

| 資料 | 來源檔 |
| --- | --- |
| 底圖、展區座標、分區放大圖 | `map/Meet 大南方地圖.jpg`(6011×3000) |
| 舞台節目表(逐字轉錄) | `schedule/活動總表.jpg` |
| 展區中英文名稱 | 上述地圖右側圖例 |

## 互動內容

- **舞台與活動空間(5)**:日光舞台、狂熱舞台、共創空間、企業媒合空間、投資媒合空間 → 點擊看 8/28(五)、8/29(六)節目表
- **展區(21)**:CX-01 ~ CX-08、EP-01 ~ EP-03、GP 國際館、H 醫療健康與高齡照護、T 風土餐桌市集、SIG、E、F、S、M、G、P → 點擊看介紹與攤位編號
- 每個項目都有第二頁「放大地圖」(右滑或按 `»`)
- 右上角清單鈕開啟完整圖例;可用 `#spot=<key>` 深層連結(例:`#spot=cx-06`)
- `?cal=1` 開啟座標校正格線,點擊會在 console 印出 viewBox 座標

## 重新產生圖片

底圖或展區位置有變更時:

```bash
python3 tools/build-assets.py     # 需要 Pillow 與 cwebp
```

會輸出 `assets/map-base.webp`(+ jpg fallback)與 26 張 `assets/zone-*.webp`,
並在 `.build/verify.png` 產生一張把所有可點擊區塊描邊的檢查圖。

座標定義在 `tools/build-assets.py` 的 `SPOTS`(以原始 6011×3000 圖的像素為單位);
`index.html` 內的 `polys` 是換算後的 viewBox 座標(`0 0 5046 2362`),兩邊需一起更新。

## 已知細節

- **底圖首次繪製**:Chrome 有機會在底圖解碼完成前就送出畫面,之後不再重繪,結果是地圖框整片空白(圖其實已經載入)。
  `index.html` 的 `ensurePainted()` 在 `img.decode()` 後改動一次 `opacity` 強制重繪,`resize` 時也會再跑一次。
  圖越大越容易發生,但**與尺寸上限無關**——單純是重繪時機。
- **換頁採直接指定 `scrollLeft`,不做動畫**:`scroll-snap-type: mandatory` 會在動畫途中把捲動位置彈回原頁。
  手指滑動的原生慣性捲動不受影響。換頁後直接呼叫 `markDots()`,不倚賴 `scroll` 事件。
