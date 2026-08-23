# 2026 Meet Greater South 亞灣新創大南方 — 互動展區地圖

**線上版:https://funtekco.github.io/meet-greater-south-2026/**

比照 `ai-taiwan-2026` 的做法,把大會地圖與舞台節目總表做成一頁式互動地圖。
單一檔案 `index.html`(無框架、無外部相依),搭配 `assets/` 內的圖片即可部署。

推送到 `main` 後由 GitHub Pages 自動發佈(來源:`main` 分支根目錄)。

## 內容來源

| 資料 | 來源檔 |
| --- | --- |
| 底圖、展區座標、分區放大圖 | `data/map/(0820更新)地圖.jpg`(5947×3000) |
| 舞台節目表(逐字轉錄) | `data/schedule/活動總表.jpg` |
| 展區中英文名稱 | 上述地圖右側圖例 |
| 參展商名錄 | `data/booth-raw/*.csv`(主辦單位匯出,未進版控) |
| 整理後名錄(PinChat AI 訓練用) | `data/booth/*.txt`(20 展區、244 家) |

參展單位 244 家 = 國內參展商 194 + 國際參展商 31 + 市集團隊 19。
`CX-08 中華民國全國中小企業總會` 為單一單位展位,主辦單位未提供名錄,不計入上述家數。

## 互動內容

- **舞台與活動空間(5)**:日光舞台、狂熱舞台、共創空間、企業媒合空間、投資媒合空間 → 點擊看 8/28(五)、8/29(六)節目表
- **展區(21)**:CX-01 ~ CX-08、EP-01 ~ EP-03、GP 國際館、H 醫療健康與高齡照護、T 風土餐桌市集、SIG、E、F、S、M、G、P → 點擊看介紹與**攤位名錄**
- **攤位名錄**:每個攤位一顆按鈕(攤位編號 + 攤商名稱),點擊在下方展開該攤商的產品與服務介紹
- 每個項目都有第二頁「放大地圖」(右滑或按 `»`)
- 右上角清單鈕開啟完整圖例;可用 `#spot=<key>` 深層連結(例:`#spot=cx-06`)
- `?cal=1` 開啟座標校正格線,點擊會在 console 印出 viewBox 座標

## 重新產生資料與圖片

**參展商資料更新時**(主辦單位寄來新的 CSV,放進 `data/booth-raw/`):

```bash
python3 tools/build-booth-data.py
```

會以 CSV 為唯一資料來源,同時重寫 `data/booth/*.txt`(含 `00_展區總覽.txt` 的加總數字)
與 `index.html` 內 `BOOTHS` 標記區塊。CSV 出現未登記的展區名會直接中止,
需先在腳本的 `ZONES` 補上「展區名 → 檔案序號 / spot key」對照。

**底圖或展區位置有變更時**:

```bash
python3 tools/build-assets.py     # 需要 Pillow 與 cwebp
```

會輸出 `assets/map-base.webp`(+ jpg fallback)與 26 張 `assets/zone-*.webp`,
並在 `.build/verify.png` 產生一張把所有可點擊區塊描邊的檢查圖。

座標定義在 `tools/build-assets.py` 的 `SPOTS`(以原始 5947×3000 圖的像素為單位);
`index.html` 內的 `polys` 是換算後的 viewBox 座標(`0 0 5025 2363`),兩邊需一起更新。
viewBox 尺寸改變時,`index.html` 有 4 處要同步:CSS `--ratio`、`.map-frame` 的
`aspect-ratio`、SVG 的 `viewBox`、JS 的 `const VB`。

底圖換版後記得同步調整 `assets/...?v=` 版本參數,舊訪客才不會拿到快取的舊地圖。

## 已知細節

- **底圖首次繪製**:Chrome 有機會在底圖解碼完成前就送出畫面,之後不再重繪,結果是地圖框整片空白(圖其實已經載入)。
  `index.html` 的 `ensurePainted()` 在 `img.decode()` 後改動一次 `opacity` 強制重繪,`resize` 時也會再跑一次。
  圖越大越容易發生,但**與尺寸上限無關**——單純是重繪時機。
- **換頁採直接指定 `scrollLeft`,不做動畫**:`scroll-snap-type: mandatory` 會在動畫途中把捲動位置彈回原頁。
  手指滑動的原生慣性捲動不受影響。換頁後直接呼叫 `markDots()`,不倚賴 `scroll` 事件。
- **同一展區多家共用一個攤位編號**:CX-01 ~ CX-07、EP-02 等主題館在主辦單位資料中,
  所有參展商共用館別編號(例:CX-02 有 21 家),攤位按鈕因此會重複顯示同一組編號,屬正常。

## 與大會地圖圖面的已知落差

主辦單位 CSV、大會地圖圖面兩邊寫法不一致的部分,已在 `tools/build-booth-data.py` 統一,
CSV 換版後會自動沿用。若之後主辦方修正了原始資料,記得回頭清掉對應的覆寫設定。

| 項目 | 地圖圖面 | 本站與 txt 採用 | 處理方式 |
| --- | --- | --- | --- |
| 攤位編號 | `E1-1`、`M1-1`、`P1-1`(圖例)、`T3-1`、`H2-1` | 一律補零兩位:`E1-01`、`M1-01`、`P1-01`、`T3-01`、`H2-01` | `pad_code()` |
| CX-07 展區名 | TTA臺灣科技新創基地 | 同左(CSV 誤植為 TAA) | `ZONE_LABEL` |
| P1-02 | 臺中軟體園區智慧創新應用加速器 | 加速器名 + 公司名「頂騰創新」兩行 | `NAME_OVERRIDE` |
| P1-04 | 造夢基地共享空間 | 公司名「易威企業」+ 品牌名兩行 | `NAME_OVERRIDE` |
| M1-01 | 正美集團 | 正美集團(CSV 為「正美企業」) | `NAME_OVERRIDE` |
| M1-02 | ACCUPASS 活動通 | ACCUPASS 活動通(CSV 為法人全名) | `NAME_OVERRIDE` |

`NAME_OVERRIDE` 只改對外顯示名稱;`data/booth/*.txt` 的「公司名稱」仍保留 CSV 原值,
另加一行「別名」把顯示名稱寫進去,PinChat 兩種講法都查得到。

尚未解決:地圖圖例的 `P1-1`~`P1-4` 與同一張圖平面圖上的 `P1-01`~`P1-04` 不一致,
`Crew Taiwan` 應為 `Creww Taiwan` —— 這兩項需主辦方修圖,本站已採正確寫法。
`CX-08 中華民國全國中小企業總會` 主辦單位未提供名錄,頁面維持顯示展區資訊條列。
