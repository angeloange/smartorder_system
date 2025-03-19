import pandas as pd
import lightgbm as lgb
from datetime import datetime
from sklearn.model_selection import train_test_split
import joblib

today_date = str(datetime.now().date()).replace('-', '_')

# 讀取 CSV 檔案
csv_file = f"predict/new_data/drink_orders_{today_date}.csv"
df = pd.read_csv(csv_file)

# 確保所有欄位名稱沒有空格
df.columns = df.columns.str.strip()

# 確保 "order_date" 是時間格式
df["order_date"] = pd.to_datetime(df["order_date"])

# 轉換日期格式
df["day_of_year"] = df["order_date"].dt.dayofyear  # 轉成數值 (例: 2025-03-01 → 60)
df["weekday"] = df["order_date"].dt.weekday  # 取得星期幾 (0=Monday, 6=Sunday)

# 新增 sales 欄位，初始值為 1
df["sales"] = 1

# 計算每一天的總銷量
df["daily_total_sales"] = df.groupby("order_date")["sales"].transform("sum")

# **依據 飲料名稱、冰塊、天氣、氣溫、日期 來合併訂單**
group_cols = ["order_date", "drink_name", "ice", "weather_status", "weather_temperature", "day_of_year", "weekday", "daily_total_sales"]
grouped_df = df.groupby(group_cols).agg({"sales": "sum"}).reset_index()

# 設定特徵與目標值
features = ["drink_name", "ice", "weather_status", "weather_temperature", "day_of_year", "weekday", "daily_total_sales"]
target = "sales"

# 轉換類別變數（LightGBM 需要 category 型別）
for col in ["drink_name", "ice", "weather_status"]:
    grouped_df[col] = grouped_df[col].astype("category")

# 分割訓練集與測試集
train_df, valid_df = train_test_split(grouped_df, test_size=0.2, random_state=42)

# 建立 LightGBM 訓練與驗證資料
train_data = lgb.Dataset(train_df[features], label=train_df[target])
valid_data = lgb.Dataset(valid_df[features], label=valid_df[target], reference=train_data)

# 設定 LightGBM 超參數
params = {
    "objective": "regression",   # 預測銷量為回歸問題
    "metric": "rmse",            # 使用 RMSE 評估
    "boosting_type": "gbdt",      # 梯度提升決策樹
    "learning_rate": 0.05,        # 學習率
    "num_leaves": 31,             # 決策樹葉子數
    "verbose": -1                 # 關閉輸出
}

# 訓練模型
print("開始訓練 LightGBM...")
callbacks = [lgb.early_stopping(50)]  # 早停策略
model = lgb.train(
    params,
    train_data,
    valid_sets=[valid_data],
    num_boost_round=500,
    callbacks=callbacks
)
print("訓練完成！")
print("Features used during training:", model.feature_name())

# 取得所有可能的飲料組合
unique_drinks = df[["drink_name", "ice", "weather_status", "weather_temperature", "day_of_year", "weekday", "daily_total_sales"]].drop_duplicates()

# 建立 DataFrame 並轉換為 category 型別
for col in ["drink_name", "ice", "weather_status"]:
    unique_drinks[col] = unique_drinks[col].astype("category")

# 進行銷量預測
unique_drinks["predicted_sales"] = model.predict(unique_drinks[features])

# 將預測值小於 0 的設為 0
unique_drinks["predicted_sales"] = unique_drinks["predicted_sales"].apply(lambda x: max(0, x))

# 儲存預測結果
unique_drinks.to_csv("drink_sales_predictions_4.csv", index=False)
print("預測結果已存入 drink_sales_predictions.csv")

# 訓練完成後存儲模型
model_filename = f"predict/sales_pred/lgbm_drink_weather_model_v4_{today_date}.pkl"
joblib.dump(model, model_filename)
print(f"模型已存入 {model_filename}")
