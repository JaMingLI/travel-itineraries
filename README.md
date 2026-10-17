# Travel Itineraries

旅遊 HTML 行程專用倉庫。GitHub Pages 與所有旅遊行程使用同一個 repo。

## 網站內容

- `index.html`：旅行列表首頁。
- `osaka-2026/index.html`：大阪・京都八日深色旅遊手冊。
- `osaka-2026/assets/`：MapLibre 程式、樣式與授權。
- `.nojekyll`：直接發布原始 HTML。

## 深色旅遊手冊

分為總覽、每日行程、地圖、費用、準備五個分頁。iPhone 使用底部固定導覽與完整目錄；每日行程一次顯示一天，日期同步至互動街道圖。完整保留 104 段時間軸、逐段至少 20% 緩衝、航班住宿及各項準備資訊。

地圖以 MapLibre GL JS 5.6.2 及 OpenFreeMap／OpenStreetMap 顯示深色向量街道，保留道路層級、路名、車站與比例尺。程式隨網站提供，街道資料需網路及支援 WebGL 的瀏覽器。地圖上的虛線只表示景點造訪順序，實際道路或鐵路導航請使用 Google Maps 連結。

以 HTTPS 網址在 iPhone Safari 開啟；「檔案」／附件預覽不是互動網站的使用入口。MapLibre 授權見 `osaka-2026/assets/MAPLIBRE-LICENSE.txt`，地圖資料來源亦顯示於地圖上。

## GitHub Pages

本 repo 使用 Deploy from a branch，分支 `main`、資料夾 `/ (root)`。不需要調整其他 repo。

## 驗證

已檢查桌面五分頁、390×844 手機版、375×667 小尺寸手機、八天切換、日期同步、目錄與 eSIM 快捷入口、歷史返回、地圖載入及定位。所有 22 個具名章節與 104 段時間軸皆保留。未進行實體 iPhone 裝置測試。

## 新增旅行

建立獨立資料夾並放入 `index.html`，再更新旅行列表首頁的連結即可。
