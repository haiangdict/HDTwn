# HDTwn 設定說明

這份文件是給你（網站維護者）看的操作說明，網站本身完全不會用到這個檔案。

## 一、用 GitHub Desktop 建立 repo 並推送

1. 在 GitHub 網站上建立一個新的 repository（例如叫 `hdtwn`），先不要勾選「加入 README」。
2. 打開 GitHub Desktop → File → Add Local Repository，選擇這個資料夾（也就是這份 zip 解壓縮後的資料夾）。
3. GitHub Desktop 會提示「這不是 git repository，要不要建立一個？」→ 選是。
4. 把 Repository 設定裡的 remote 指到你剛建立的 GitHub repo（Repository → Repository Settings → Remote），或者在建立本地 repo 時直接選擇 publish 到你剛建立的那個 repo。
5. Commit 全部檔案，Push 到 GitHub。
6. 到 repo 的 Settings → Pages，Source 選「Deploy from a branch」，Branch 選 `main` / `/(root)`，存檔。等一兩分鐘後，網站就會在 `https://<你的帳號>.github.io/<repo名稱>/` 上線。

## 二、設定 GitHub secret（讓自動同步 Google Sheets 能運作）

網站資料是靠 `.github/workflows/sync-sheets.yml` 這個排程（預設每 6 小時一次，也可以在 GitHub 網頁上手動觸發）去讀取四份 Google Sheet、寫回 `data/*.csv`，然後網站直接讀本地的這幾個 CSV 檔（不會即時打 Google API，速度快、也不怕額度用完）。

要讓這個排程能讀到 Google Sheet，需要兩件事：

### 1. 把四份 Google Sheet 共用給服務帳號

你提到目前的自動同步帳號是：

```
hlddru-sheets-reader@hlddru.iam.gserviceaccount.com
```

請確認下面四份 Google Sheet 都已經「共用」給這個 email，權限「檢視者」即可：

- TWN-Lemmata：`1PfpINRZEZ8duVSQao7LeCkUqjcW4Ly6R9OyNod7N5dg`
- TWN_Senses：`1_7ylGQXn49CDqxwd559N2d8iva6lJveqUNjr4UF728M`
- TWN-Examples：`1PDIBQpzsK4L59DQXE4MduBUW0o2rOVXOqV_S8m8I_OE`
- HLD-Etymology：`1TkZF2NUeGGMMWel48AMZFZ2uCdjiACh3o3CC0vgvglU`

如果這個服務帳號已經在幫 HLDKor（韓語辭典）做同樣的事，很可能這四份也已經共用過了；沒有的話就到每份 Sheet 右上角「共用」，貼上上面的 email，設「檢視者」。

### 2. 把服務帳號金鑰存成 repo secret

1. 找到這個服務帳號的金鑰 JSON 檔（如果 HLDKor 那邊已經有在用，直接沿用同一把金鑰即可，不需要重新產生）。
2. 到 GitHub repo 頁面 → Settings → Secrets and variables → Actions → New repository secret。
3. Name 填：`GOOGLE_SERVICE_ACCOUNT_KEY`
4. Secret 內容：把整份金鑰 JSON 檔的內容完整貼進去（是一整包 `{...}` JSON，不是檔案路徑）。
5. 存檔。

設定好之後，可以到 repo 的 Actions 分頁，找到「Sync Google Sheets data」這個 workflow，按「Run workflow」手動跑一次，確認 `data/` 底下的 CSV 有被正確更新、沒有紅色錯誤。

### 關於「分頁名稱」

`scripts/sync_sheets.py` 裡預設抓的分頁名稱是 `TWN-Lemmata`、`TWN_Senses`、`TWN-Examples`、`HLD-Etymology`（沿用你提供的名稱）。如果 Google Sheet 裡實際的分頁名稱跟這個不同，打開 `scripts/sync_sheets.py`，把 `SHEETS` 這個清單裡對應的 `sheetName` 改成正確的分頁名稱即可。

## 三、待補項目

網站已經可以完整運作（詞目瀏覽、搜尋、分類篩選、TL/POJ 切換等都已測試過），但下面兩項目前是先做成佔位設定，需要你補上實際值：

### 1. 音檔網域

`index.html` 裡的這一行（搜尋 `AUDIO_BASE_URL` 就找得到）：

```js
const AUDIO_BASE_URL = '';
```

目前是空字串，所以播放鍵會顯示為停用（灰色 `—`）。等你確認 Cloudflare 那邊音檔的公開網域後，把網址填進去即可（不要加結尾斜線），例如：

```js
const AUDIO_BASE_URL = 'https://audio.example.com';
```

程式會自動組成 `https://audio.example.com/TWN/Lemmata/檔名.mp3`（詞目音檔）和 `https://audio.example.com/TWN/Examples/檔名.mp3`（例句音檔），不用再改其他地方。

### 2. 方言分布圖卡連結

義項裡「方言差」欄位（如 `V743`）目前點下去會開一個新分頁，顯示「即將推出」的佔位頁面（`maps/stub.html`）。等 982 張圖卡系統確定部署位置後，有兩個做法：

- **最簡單**：如果圖卡系統最後就是放在這個網站底下的某個路徑（例如 `/maps/743.html`），把 `index.html` 裡 `buildDialDiffHtml()` 函式裡的
  ```js
  href="./maps/stub.html?id=${num}"
  ```
  改成
  ```js
  href="./maps/${num}.html"
  ```
  然後把 982 張圖卡檔案放進 `maps/` 資料夾即可。
- **圖卡系統部署在別的網域**：把上面那行的 `href` 改成組合完整外部網址的邏輯，例如 `href="https://your-maps-site.com/card/${num}"`。

### 3. 版權聲明的資料來源

`about.html` 裡有兩處用 `〔待填〕` 標示（黃色文字），是台語詞彙資料的實際來源機構名稱與授權連結，我沒有自行假設是哪個單位，需要你確認後填入。

## 四、其他你可能想調整的地方

- `about.html` 目前沿用跟 HLDKor 相同的 Formspree 表單 ID（`mzdkqybd`），兩邊回報訊息會混在同一個收件匣。如果想分開，去 https://formspree.io 另建一個表單，把 `about.html` 裡的 `FORMSPREE_ID` 換掉即可。
- 字母索引目前是以「TL 拼音字首」分組（a-z，不隨 TL/POJ 切換而改變），這是我依照台羅字典常見的排序慣例做的預設選擇，如果你有其他排序想法（例如依漢字部首、依 POJ 拼音），之後可以再調整 `firstLetter()` 這個函式。
- 附註欄位裡如果出現像 `{1658}` 這種花括號編號引用，目前是當作純文字顯示，還沒有自動轉成可點擊連結；如果你想要這個功能，之後可以再加。
- 詞目卡片右上角原本 HLDKor 版本有「截圖分享」按鈕，這版先拿掉了，如果想要可以之後再加回來。
