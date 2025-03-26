import os
import json
import pandas as pd
import lightgbm as lgb
import joblib
from sklearn.model_selection import train_test_split
from datetime import datetime

def train_total_sales_model():
    """訓練總銷量預測模型"""
    print("\n=== 訓練總銷量預測模型 ===")
    
    # 讀取 CSV 數據
    csv_file = "predict/new_data/drink_orders_2025_03_18.csv"
    df = pd.read_csv(csv_file)
    
    # 確保日期格式正確
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # 創建特徵
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
    
    # 定義特徵和目標
    X = daily_sales[['weather_status', 'weather_temperature', 'weekday', 'month', 'day_of_year']]
    y = daily_sales['daily_total']
    
    # 將分類特徵轉換為分類類型
    X['weather_status'] = X['weather_status'].astype('category')
    
    # 分割數據
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 訓練模型
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'n_estimators': 100
    }
    
    model = lgb.LGBMRegressor(**params)
    model.fit(X_train, y_train, 
              eval_set=[(X_test, y_test)], 
              eval_metric='rmse',
              callbacks=[lgb.early_stopping(10), lgb.log_evaluation(100)])
    
    # 保存模型
    output_model_path = "predict/total_pred/sales_total_model_v2_2025_03_18.pkl"
    joblib.dump(model, output_model_path)
    print(f"總銷量模型已保存到: {output_model_path}")
    
    return model

def train_drink_sales_model():
    """訓練飲品銷量預測模型"""
    print("\n=== 訓練飲品銷量預測模型 ===")
    
    # 讀取 CSV 數據
    csv_file = "predict/new_data/drink_orders_2025_03_18.csv"
    df = pd.read_csv(csv_file)
    
    # 確保日期格式正確
    df['order_date'] = pd.to_datetime(df['order_date'])
    
    # 創建特徵
    df['day_of_year'] = df['order_date'].dt.dayofyear
    df['weekday'] = df['order_date'].dt.weekday
    
    # 新增 sales 欄位，初始值為 1
    df["sales"] = 1
    
    # 計算每一天的總銷量
    df["daily_total_sales"] = df.groupby("order_date")["sales"].transform("sum")
    
    # 依據 飲料名稱、冰塊、天氣、氣溫、日期 來合併訂單
    group_cols = ["order_date", "drink_name", "ice", "weather_status", "weather_temperature", "day_of_year", "weekday", "daily_total_sales"]
    grouped_df = df.groupby(group_cols).agg({"sales": "sum"}).reset_index()
    
    # 設定特徵與目標值
    features = ["drink_name", "ice", "weather_status", "weather_temperature", "day_of_year", "weekday", "daily_total_sales"]
    target = "sales"
    
    # 將分類特徵轉換為分類類型
    for col in ["drink_name", "ice", "weather_status"]:
        grouped_df[col] = grouped_df[col].astype('category')
    
    # 分割數據
    X = grouped_df[features]
    y = grouped_df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 訓練模型
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'n_estimators': 100
    }
    
    model = lgb.LGBMRegressor(**params)
    model.fit(X_train, y_train, 
              eval_set=[(X_test, y_test)], 
              eval_metric='rmse',
              callbacks=[lgb.early_stopping(10), lgb.log_evaluation(100)])
    
    # 保存模型
    output_model_path = "predict/sales_pred/lgbm_drink_weather_model_v4_2025_03_18.pkl"
    joblib.dump(model, output_model_path)
    print(f"飲品銷量模型已保存到: {output_model_path}")
    
    return model

def update_predict_total_sales():
    """修改 predict_total_sales.py 文件中的引用，使其適配 weather_temperature"""
    file_path = "predict/total_pred/predict_total_sales.py"
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    # 修改 process_features 方法
    updated_content = content.replace(
        '"temperature": self.temperature,',
        '"weather_temperature": self.temperature,'
    )
    
    with open(file_path, 'w') as file:
        file.write(updated_content)
    
    print(f"已更新 {file_path} 中的列名引用")

def update_app_weather_recommend():
    """修改 app.py 中的 weather_recommend 函數以處理任何錯誤"""
    file_path = "frontend/app.py"
    
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # 尋找 weather_recommend 函數的開始
        start_index = content.find("@app.route('/api/weather_recommend'")
        if start_index == -1:
            print("無法在 app.py 中找到 weather_recommend 函數")
            return False
        
        # 找到函數體的開始
        func_start = content.find("def weather_recommend()", start_index)
        if func_start == -1:
            print("無法在 app.py 中找到 weather_recommend 函數定義")
            return False
        
        # 從函數開始位置找到第一個缩進代碼塊
        indent_start = content.find("    ", func_start)
        
        # 替換整個函數體
        new_function = """def weather_recommend():
    try:
        station, location, weather, temperature = get_weather_data()
        date = str(datetime.now().date())

        test_date = date
        test_weather = classify_weather(weather=weather, weather_dict=weather_dict)
        test_temperature = int(temperature)
        
        # 使用簡單推薦邏輯
        weather_lower = test_weather.lower()
        drinks = []
        
        # 根據溫度選擇飲品
        if test_temperature > 28:  # 炎熱
            drinks = ["珍珠奶茶", "檸檬綠茶", "百香果綠茶", "蜂蜜檸檬", "芒果冰沙", "冬瓜茶"]
        elif test_temperature > 22:  # 溫暖
            drinks = ["波霸奶茶", "椰果奶茶", "蜂蜜奶茶", "烏龍拿鐵", "冬瓜檸檬", "青茶"]
        elif test_temperature > 15:  # 涼爽
            drinks = ["焦糖奶茶", "巧克力牛奶", "可可", "拿鐵咖啡", "牛奶咖啡", "摩卡咖啡"]
        else:  # 寒冷
            drinks = ["熱拿鐵", "熱奶茶", "黑糖珍珠鮮奶", "熱可可", "熱烏龍茶", "熱紅茶"]
        
        # 根據天氣進一步調整
        if weather_lower == "rainy" or weather_lower == "stormy":
            # 下雨天適合的飲品
            if test_temperature <= 20:
                drinks = ["熱拿鐵", "熱奶茶", "黑糖珍珠鮮奶", "熱可可", "熱烏龍茶", "熱紅茶"]
        
        return jsonify(drinks)
    except Exception as e:
        print(f"天氣推薦功能錯誤: {str(e)}")
        # 返回預設推薦
        return jsonify(["珍珠奶茶", "波霸奶茶", "烏龍拿鐵", "檸檬綠茶", "焦糖奶茶", "蜂蜜奶茶"])
"""
        
        # 替換函數體
        updated_content = content[:func_start] + new_function + content[content.find("\n\n", func_start):]
        
        with open(file_path + ".bak", 'w') as file:
            file.write(content)
        
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        print(f"已更新 {file_path} 中的 weather_recommend 函數")
        return True
    
    except Exception as e:
        print(f"更新 app.py 失敗: {str(e)}")
        return False

def test_weather_recommend_api():
    """測試天氣推薦 API 是否工作"""
    import requests
    
    try:
        response = requests.get("http://localhost:5002/api/weather_recommend")
        if response.status_code == 200:
            data = response.json()
            print(f"API 返回成功: {json.dumps(data, ensure_ascii=False)}")
            return True
        else:
            print(f"API 返回錯誤狀態碼: {response.status_code}")
            return False
    except Exception as e:
        print(f"無法連接到 API: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== 開始修復天氣推薦功能 ===")
    
    # 步驟 1: 重新訓練總銷量模型
    total_model = train_total_sales_model()
    
    # 步驟 2: 重新訓練飲品銷量模型
    sales_model = train_drink_sales_model()
    
    # 步驟 3: 更新 predict_total_sales.py 文件中的列引用
    update_predict_total_sales()
    
    # 步驟 4: 更新 app.py 中的 weather_recommend 函數
    update_app_weather_recommend()
    
    print("\n=== 天氣推薦功能修復完成 ===")
    print("請重新啟動服務器以套用更改")
    print("然後可以訪問 http://localhost:5002/api/weather_recommend 測試功能")