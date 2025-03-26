import os
import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import train_test_split

def train_and_fix_models():
    """訓練模型並修復列名問題"""
    print("=== 開始修復智慧點餐推薦系統 ===")
    
    # 1. 讀取CSV文件
    csv_file = "predict/new_data/drink_orders_2025_03_18.csv"
    df = pd.read_csv(csv_file)
    print(f"成功讀取CSV: {csv_file}")
    print(f"CSV列名: {df.columns.tolist()}")
    
    # 2. 訓練總銷量模型
    print("\n訓練總銷量預測模型...")
    train_total_model(df)
    
    # 3. 訓練飲品銷量模型
    print("\n訓練飲品銷量預測模型...")
    train_sales_model(df)
    
    # 4. 修正預測腳本中的列名引用
    fix_column_names()
    
    print("\n=== 修復完成! ===")
    print("模型已成功重新訓練，列名引用已修正")
    print("請重新啟動服務器以套用更改")

def train_total_model(df):
    """訓練總銷量預測模型"""
    # 基本數據處理
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['day_of_year'] = df['order_date'].dt.dayofyear
    df['weekday'] = df['order_date'].dt.weekday
    df['month'] = df['order_date'].dt.month
    
    # 計算每日總銷量
    df['sales'] = 1
    daily_sales = df.groupby('order_date').agg({
        'sales': 'sum',
        'weather_status': 'first',
        'weather_temperature': 'first',
        'day_of_year': 'first',
        'weekday': 'first',
        'month': 'first'
    }).reset_index()
    
    daily_sales.rename(columns={'sales': 'daily_total'}, inplace=True)
    
    # 準備特徵和目標
    X = daily_sales[['weather_status', 'weather_temperature', 'weekday', 'month', 'day_of_year']]
    y = daily_sales['daily_total']
    
    # 將分類特徵轉換為分類類型
    X = X.copy()
    X['weather_status'] = X['weather_status'].astype('category')
    
    # 分割數據
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 訓練模型
    model = lgb.LGBMRegressor(
        objective='regression',
        metric='rmse',
        boosting_type='gbdt',
        num_leaves=31,
        learning_rate=0.05,
        feature_fraction=0.9,
        n_estimators=100
    )
    
    # 使用最簡單的訓練方式避免參數兼容問題
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)])
    
    # 保存模型
    output_path = "predict/total_pred/sales_total_model_v2_2025_03_18.pkl"
    joblib.dump(model, output_path)
    print(f"總銷量模型已保存到: {output_path}")

def train_sales_model(df):
    """訓練飲品銷量預測模型"""
    # 基本數據處理
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['day_of_year'] = df['order_date'].dt.dayofyear
    df['weekday'] = df['order_date'].dt.weekday
    
    # 計算銷量
    df['sales'] = 1
    df["daily_total_sales"] = df.groupby("order_date")["sales"].transform("sum")
    
    # 依據 飲料名稱、冰塊、天氣、氣溫、日期 來合併訂單
    group_cols = ["order_date", "drink_name", "ice", "weather_status", "weather_temperature", 
                  "day_of_year", "weekday", "daily_total_sales"]
    grouped_df = df.groupby(group_cols).agg({"sales": "sum"}).reset_index()
    
    # 準備特徵和目標
    features = ["drink_name", "ice", "weather_status", "weather_temperature", 
                "day_of_year", "weekday", "daily_total_sales"]
    target = "sales"
    
    # 將分類特徵轉換為分類類型
    grouped_df = grouped_df.copy()
    for col in ["drink_name", "ice", "weather_status"]:
        grouped_df[col] = grouped_df[col].astype('category')
    
    # 分割數據
    X = grouped_df[features]
    y = grouped_df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 訓練模型
    model = lgb.LGBMRegressor(
        objective='regression',
        metric='rmse',
        boosting_type='gbdt',
        num_leaves=31,
        learning_rate=0.05,
        feature_fraction=0.9,
        bagging_fraction=0.8,
        n_estimators=100
    )
    
    # 使用最簡單的訓練方式避免參數兼容問題
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)])
    
    # 保存模型
    output_path = "predict/sales_pred/lgbm_drink_weather_model_v4_2025_03_18.pkl"
    joblib.dump(model, output_path)
    print(f"飲品銷量模型已保存到: {output_path}")

def fix_column_names():
    """修正預測腳本中的列名引用，使用 weather_temperature 而非 temperature"""
    # 修正總銷量預測腳本
    total_pred_path = "predict/total_pred/predict_total_sales.py"
    with open(total_pred_path, 'r') as file:
        content = file.read()
    
    updated_content = content.replace(
        '"temperature": self.temperature,',
        '"weather_temperature": self.temperature,'
    )
    
    with open(total_pred_path, 'w') as file:
        file.write(updated_content)
    print(f"已修正 {total_pred_path} 中的列名引用")
    
    # 修正飲品銷量預測腳本
    sales_pred_path = "predict/sales_pred/predict_sales_v4_2.py"
    with open(sales_pred_path, 'r') as file:
        content = file.read()
    
    updated_content = content.replace(
        'predict_df["temperature"] = self.temperature',
        'predict_df["weather_temperature"] = self.temperature'
    )
    
    with open(sales_pred_path, 'w') as file:
        file.write(updated_content)
    print(f"已修正 {sales_pred_path} 中的列名引用")

if __name__ == "__main__":
    train_and_fix_models()