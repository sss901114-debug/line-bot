# 📲 LINE 自動推播財經機器人

每天自動將市場資訊推播到你的 LINE，共三個時間點。

---

## 📋 推播內容

| 時間 | 內容 |
|------|------|
| 🌅 07:00 | 美股四大指數、黃金/銅/油/比特幣/美元指數、近3個月走勢圖、供需缺貨相關新聞 |
| ☀️ 15:00 | 台灣 Google 熱搜關鍵字 Top 10 |
| 🌆 19:00 | 台股盤後：融資融券增減、外資投信買賣超、大盤/櫃買指數、類股漲跌、熱門個股、公開資訊觀測站重大訊息 |

---

## 🚀 快速開始

### Step 1：申請 LINE Messaging API

1. 前往 [LINE Developers](https://developers.line.biz/)
2. 登入後建立 **Provider** → 建立 **Messaging API Channel**
3. 到 Channel 設定頁面：
   - 取得 **Channel Access Token**（長期）
   - 取得自己的 **User ID**（從 LINE Official Account Manager 或用 webhook 取得）
4. 將 Messaging API 設定為 **Push message** 模式（不需要 webhook）

> 💡 **取得你的 User ID：**  
> 在 LINE Developers → Basic settings 找到「Your user ID」，即為 `U` 開頭的字串。

### Step 2：申請 Cloudinary（走勢圖圖片托管）

1. 前往 [cloudinary.com](https://cloudinary.com/) 免費註冊
2. 從 Dashboard 取得：
   - Cloud Name
   - API Key
   - API Secret

### Step 3：設定環境變數

複製 `.env.example` 為 `.env`，填入你的憑證：

```bash
cp .env.example .env
# 然後編輯 .env 填入所有金鑰
```

### Step 4：安裝相依套件

```bash
pip install -r requirements.txt
```

### Step 5：測試執行

```bash
# 測試早報
python scripts/morning.py

# 測試午報
python scripts/afternoon.py

# 測試晚報
python scripts/evening.py
```

---

## ☁️ 部署方式

### 方案 A：GitHub Actions（推薦，免費）

最簡單的方式，完全在雲端運行，不需要自己的伺服器。

1. 將專案 push 到 GitHub
2. 到 GitHub Repository → **Settings → Secrets and variables → Actions**
3. 新增以下 Secrets：

| Secret 名稱 | 說明 |
|-------------|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Token |
| `LINE_TARGET_IDS` | 你的 LINE User ID |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary Cloud Name |
| `CLOUDINARY_API_KEY` | Cloudinary API Key |
| `CLOUDINARY_API_SECRET` | Cloudinary API Secret |

4. 排程已設定在 `.github/workflows/line_bot.yml`，push 後自動生效
5. 可到 **Actions** 頁面手動觸發測試

> ⚠️ **注意**：GitHub Actions 免費方案每月 2000 分鐘，三個 job 每天約用 6-10 分鐘，一個月約 200-300 分鐘，完全夠用。

---

### 方案 B：本機持續運行（Raspberry Pi / 個人電腦）

```bash
# 安裝後直接執行排程器
python scheduler.py
```

建議用 `screen` 或 `nohup` 讓它在背景持續運行：

```bash
# 使用 screen
screen -S linebot
python scheduler.py
# Ctrl+A, D 可以 detach
```

---

### 方案 C：Railway / Render（輕量雲端）

1. 連結 GitHub Repository
2. 部署時選擇 `python scheduler.py` 為啟動指令
3. 設定環境變數（與 GitHub Secrets 相同的 key/value）
4. Railway 免費方案每月 $5 額度，足夠運行

---

## 📁 專案結構

```
line_bot/
├── .env.example              # 環境變數範本
├── .env                      # 實際設定（不要 commit！）
├── requirements.txt          # Python 套件需求
├── scheduler.py              # 本機排程器（本機部署用）
├── .github/
│   └── workflows/
│       └── line_bot.yml      # GitHub Actions 排程（雲端部署用）
└── scripts/
    ├── line_push.py          # LINE API 推播工具
    ├── morning.py            # 07:00 美股/商品報告
    ├── afternoon.py          # 15:00 Google 熱搜
    └── evening.py            # 19:00 台股盤後報告
```

---

## 🔧 常見問題

**Q：台股資料抓不到？**  
A：證交所 API 通常在收盤後 1-2 小時才完整，晚報定在 19:00 是為了確保資料就緒。如果還是空的，可以調整至 19:30。

**Q：走勢圖無法推播？**  
A：確認 Cloudinary 憑證正確，且帳號在免費額度內。每月上傳 25GB，每天一張圖幾乎不會超額。

**Q：Google Trends 有時抓不到？**  
A：Google 會限制爬取頻率，程式已做備援切換（RSS → pytrends）。偶爾失敗屬正常。

**Q：LINE 顯示「The request body has 1 error(s)」？**  
A：通常是 Channel Access Token 過期或格式錯誤，重新到 LINE Developers 複製長期 token。

**Q：如何加入群組推播？**  
A：在群組中將 Bot 加為成員，取得 Group ID（C 開頭），加到 `LINE_TARGET_IDS` 並用逗號分隔多個 ID。

---

## 📌 資料來源

- 美股指數：Yahoo Finance (`yfinance`)
- 大宗商品：Yahoo Finance
- 比特幣：Yahoo Finance / CoinGecko
- Google 熱搜：Google Trends RSS
- 台股資料：臺灣證券交易所 (TWSE) 公開 API
- 重大訊息：公開資訊觀測站 (MOPS)
- 新聞：Google News RSS

---

## ⚖️ 注意事項

- 本系統資料來源均為公開資訊，僅供個人參考用途
- 不構成任何投資建議
- 請遵守各資料來源的使用條款
