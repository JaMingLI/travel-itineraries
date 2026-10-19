# 大阪・京都旅遊手冊

正式網址：https://jamingli.github.io/travel-itineraries/osaka-2026/

本機預覽：http://127.0.0.1:8766/osaka-map-preview/

## 維護方式

- `src/days/day-01.html`～`day-08.html`：每日行程的權威來源，保留原始內容。
- `src/pages/`：總覽、每日行程外框、地圖、費用、準備五個分頁。
- `src/document.html`：文件外框及資源載入位置。
- `src/styles/`：13份原始樣式，依原來的順序載入，保留原有視覺與響應式斷點。`src/data/style-layers.json` 記錄原始雜湊。
- `src/scripts/`：展開收合、列印、地圖、分頁、清單及清單狀態遷移。
- `src/data/`：地圖座標與原始清單資料；座標需另行核實，不從店名推測。
- `sync.py`：從每日行程擷取標題、日期、餐點時間、交通導航及費用，產生其他分頁的摘要。
- `assets/data/itinerary.json`：產生的結構化行程資料，方便核對，不是另一份手動維護來源。
- `index.html`、`assets/css/`、`assets/js/`：產生成品，請不要直接修改。

執行環境 Python 3.10+、Beautiful Soup；測試另需 Node.js。瀏覽器本身不需要 Python、Node、框架或建置服務。

```sh
python3 -m pip install -r requirements.txt
python3 build.py
python3 build.py --check
python3 -m unittest discover -s tests -v
node tests/checklist-state.test.js
```

`build.py --preserve-content` 僅供第一階段抽取比對，會略過資料同步，不應拿來發布。正式成品使用預設建置。

`build.py --mirror <發布資料夾>` 可同步部署檔案，但不會上傳。GitHub Pages 必須一起發布 `index.html` **及整個 assets/**，不可只上傳 HTML。舊的章節錨點及 localStorage 清單識別碼保持不變。

## 本次同步內容

- 總覽八天標題、路線摘要與晚餐時間依每日行程產生，Day 8 移除舊「慢早餐」安排。
- 航班銜接說明同步 Day 8 10:00退房、12:30取件、13:15出發、15:15到航廈的規劃。
- Day 6 地圖補一笑燒肉座標；各日導航連結與行程卡一致，文字明示其開啟的路段。
- 準備清單統一 Tottotto 18:00到附近、18:15報到、18:30–20:30用餐，並同步豬一候位及USJ晚餐／蛋糕取貨。
- 準備指南的回程取件與USJ蛋糕動線同步更新；京都公車費明示為雨天備案。
- 每日及總預算改由行程卡計算；餐費仍¥98,000，交通／餐飲／門票合計¥143,300，匯率假設0.22。
- 清單預設內容更新時，只遷移仍等於舊預設的欄位；保留打勾、私人編輯及自訂事項。

## 驗證與限制

第一階段內容DOM完全一致；15個CSS項目（含內嵌備用樣式及MapLibre）內容與載入順序一致。每日八份來源片段與110段時間軸在同步後也原封保留；補充說明預設收合。

自動測試涵蓋擷取一致性、分頁同步、地圖店面／導航、金額、重複建置及清單遷移；瀏覽器檢查390×844與1280×900五個分頁均無水平溢出，打勾後重整保留，編輯視窗及互動地圖正常，未見JavaScript錯誤。這不等於實體iPhone驗證，也不宣稱所有動態畫面逐像素一致。

地圖 MapLibre GL JS 5.6.2，底圖 OpenFreeMap／OpenStreetMap，需要網路及WebGL。虛線為造訪順序，實際交通請開啟Google Maps。iPhone使用Safari網址開啟，勿用「檔案」或附件預覽。授權見 `assets/MAPLIBRE-LICENSE.txt`。
