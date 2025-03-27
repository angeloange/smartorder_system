from datetime import datetime
import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

today_date = str(datetime.now().date()).replace('-', '_')

# 讀取 CSV 檔案
df = pd.read_csv("predict/new_data/drink_orders_2025_03_18.csv")

# **建立 weather_status 類別對應表**
df["weather_status"] = df["weather_status"].astype("category")
weather_mapping = dict(enumerate(df["weather_status"].cat.categories))
print(f"天氣狀態編碼對應表：{weather_mapping}")

# **轉換 weather_status 為數字**
df["weather_status"] = df["weather_status"].cat.codes

# 轉換 order_date 成 datetime 格式
df["order_date"] = pd.to_datetime(df["order_date"])

# 加入「星期幾」特徵（0=星期一，6=星期日）
df["weekday"] = df["order_date"].dt.weekday

# **加入「月份」特徵**
df["month"] = df["order_date"].dt.month

# **加入「一年內的第幾天」特徵**
df["day_of_year"] = df["order_date"].dt.dayofyear

# 計算每天的銷量（使用相同日期的筆數來表示銷量）
df["daily_sales"] = df.groupby("order_date")["order_date"].transform("count")

# 移除重複的日期記錄，確保每個日期只出現一次
df = df.drop_duplicates(subset=["order_date"])

# 定義特徵與目標
features = ["weather_status", "weather_temperature", "weekday", "month", "day_of_year"]
target = "daily_sales"

X = df[features]
y = df[target]

# 切分訓練集與測試集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 訓練 LightGBM 模型
model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1)
model.fit(X_train, y_train)

# 預測測試集
y_pred = model.predict(X_test)

# 計算誤差
mae = mean_absolute_error(y_test, y_pred)
print(f"模型誤差（MAE）：{mae:.2f}")

# 測試預測範例（假設晴天 + 28°C + 星期三 + 7 月 + 200 天）
sample_data = pd.DataFrame({"weather_status": [0], "weather_temperature": [28], "weekday": [2], "month": [7], "day_of_year": [200]})
predicted_sales = model.predict(sample_data)
print(f"預測銷量（晴天 + 28°C + 7 月 + 星期三 + 一年內第 200 天）：{predicted_sales[0]:.0f} 杯")

# 訓練完成後存儲模型
model_filename = "sales_total_model_v2_2025_03_18.pkl"
joblib.dump(model, model_filename)
print(f"模型已存入 {model_filename}")
