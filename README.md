# Travel Itineraries

旅遊 HTML 行程專用倉庫。GitHub Pages 與行程檔案使用同一個 repo。

## 網站內容

- `index.html`：旅行列表首頁。
- `osaka-2026/index.html`：大阪・京都八日互動行程，包含每日時間軸、20% 緩衝與街道地圖。
- `.nojekyll`：以原始 HTML 直接發布。
- `LEAFLET-LICENSE.txt`：互動地圖程式授權。

## GitHub Pages

在本 repo 的 Settings → Pages，選擇 Deploy from a branch，分支 `main`、資料夾 `/ (root)`。不需要更動其他 repo。

以發布後的 HTTPS 網址在 iPhone Safari 開啟。iOS「檔案」／附件預覽不是完整的互動網站執行環境。

## 地圖

Leaflet 1.9.4 隨 HTML 內嵌，無需 WebGL，也不依賴外部程式庫 CDN。街道圖磚由日本國土地理院即時提供，需網路連線。行程虛線表示造訪順序，不代表實際道路或鐵路路線。

## 新增旅行

每次旅行建立一個新資料夾並放入 `index.html`，再更新首頁連結即可。正式發布前確認選定的公開內容版本。
