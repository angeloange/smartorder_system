# 智慧飲料點餐系統

<img alt="版本" src="https://img.shields.io/badge/版本-1.0.0-blue">
<img alt="Python" src="https://img.shields.io/badge/Python-3.8+-green">
<img alt="Flask" src="https://img.shields.io/badge/Flask-2.2.3-orange">
<img alt="OpenAI" src="https://img.shields.io/badge/OpenAI-API-purple">

一個結合自然語言處理的飲料店點餐系統，包含前台點餐介面和後台管理系統。透過AI技術提供智能化點餐體驗，並為店家提供高效管理工具。
## 簡報連結: https://pse.is/智慧點餐系統
## ✨ 核心功能

### 🤖 AI 智能點餐
- **自然語言理解**：直接用口語表達訂購飲料，如「我要一杯大杯珍珠奶茶微糖少冰」
- **智能助手**：AI 聊天機器人協助點餐，並能回答菜單相關問題
- **語音識別**：支援語音輸入，無需手動輸入文字

### 🖥️ 雙系統架構
- **顧客前台**：直覺化操作界面，多模態互動方式
- **店家後台**：高效訂單處理、銷售統計和庫存管理

### 📊 數據驅動
- **即時統計**：實時更新銷售數據與熱門產品
- **預測分析**：基於歷史與天氣數據預測銷量趨勢
- **客製化推薦**：智能推薦適合當下的飲品

## 🔧 技術架構

### 前端技術
- HTML5、CSS3、JavaScript
- Socket.IO 客戶端
- Azure Speech SDK

### 後端技術
- Flask 網頁框架
- OpenAI API
- Azure 語音服務
- SQLAlchemy ORM
- EventLet

### 數據分析
- Scikit-learn
- Pandas
- NumPy

## 📋 安裝步驟

### 系統需求
- Python 3.8+
- MySQL 5.7+
- 有效的 OpenAI API 金鑰
- 有效的 Azure Speech API 金鑰（可選）

### 安裝流程

1. **複製專案**
```bash
git clone https://github.com/yourusername/beverage-ordering-system.git
cd beverage-ordering-system
```

2. **建立虛擬環境**
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows
```

3. **安裝相依套件**
```bash
pip install -r requirements.txt
```

4. **設定環境變數**

在專案根目錄建立 `.env` 檔案，填入以下內容：
```
DB_USER='your_db_user'
DB_PASSWORD='your_db_password'
DB_HOST='localhost'
DB_NAME='beverage_db'
DB_PORT='3306'
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY='your_secret_key'
OPENAI_API_KEY='your_openai_api_key'
AZURE_SPEECH_KEY='your_azure_speech_key'
AZURE_SPEECH_REGION='eastasia'
```

5. **啟動系統**

方法一：一鍵啟動
```bash
python run.py
```

方法二：分別運行
```bash
# 前台
python -m frontend.app

# 後台
python -m admin_backend.app
```

成功啟動後：
- 前台系統：http://localhost:5002
- 後台系統：http://localhost:5003

## 📱 系統功能說明

### 前台功能
- **自然語言點餐介面**：透過聊天形式直接描述訂單
- **語音辨識點餐**：支援語音輸入，便利無接觸操作
- **訂單即時狀態查詢**：實時追蹤訂單處理進度
- **多模態互動**：文字、語音、按鈕多種交互方式
- **天氣智能推薦**：根據當天天氣推薦適合的飲品

### 後台功能
- **訂單管理與處理**：一站式查看和更新訂單狀態
- **批量訂單操作**：高效處理多筆訂單
- **銷售數據分析**：視覺化報表呈現銷售趨勢
- **庫存管理**：追蹤原料使用和補貨需求
- **訂單號碼系統**：自動生成格式為 mmddX#-Y 的訂單號碼
  - mmdd：月份和日期 (例如：0324)
  - X：大寫字母 A-Z
  - #：數字 1-9
  - Y：訂單內的品項序號

## 🔍 系統目錄結構

```
beverage-ordering-system/
├── frontend/                # 前台系統
│   ├── app.py              # 主應用程式
│   ├── order_analyzer.py   # 訂單分析器
│   ├── codes/              # 功能模組
│   ├── static/             # 靜態檔案
│   └── templates/          # 網頁模板
├── admin_backend/          # 後台系統
│   ├── app.py              # 後台主應用程式
│   ├── models/             # 資料模型
│   └── templates/          # 後台界面模板
├── tools/                  # 共用工具
├── predict/                # 預測模型
│   ├── models.py           # 預測模型定義
│   ├── total_pred/         # 總銷量預測
│   └── sales_pred/         # 品項銷量預測
├── chat_tools/             # 聊天分析工具
├── weather_API/            # 天氣 API 整合
├── requirements.txt        # 相依套件清單
├── run.py                  # 主啟動腳本
└── README.md               # 說明文件
```

## ❓ 常見問題

### SECRET_KEY 是什麼？
這是 Flask 用來加密 session 資料的金鑰。可以使用以下指令生成：
```python
import secrets
secrets.token_hex(32)
```

### 資料庫連接失敗？
- 確認 MySQL 服務是否運行中
- 檢查 `.env` 中的資料庫設定是否正確
- 確認資料庫使用者有適當的權限

### 語音功能無法使用？
- 確認瀏覽器允許麥克風權限
- 檢查 Azure 語音服務金鑰是否正確
- 使用 Chrome 或 Edge 等現代瀏覽器

### 訂單確認失敗？
- 確認前後端連接正常
- 檢查後端日誌以獲取詳細錯誤信息
- 可能是訂單號碼生成問題，嘗試清除重複路由定義

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 LICENSE 文件
