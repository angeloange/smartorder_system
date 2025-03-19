import pandas as pd
import joblib
from predict.models import Pred_sales


class Pred_Sales:
    def __init__(self,pred_info: Pred_sales):
        self.date_string = pred_info.date_string
        self.weather = pred_info.weather
        self.temperature = pred_info.temperature
        self.daily_total_sales = pred_info.daily_total_sales
        self.model_filename = pred_info.model_filename
        self.csv_filename = pred_info.csv_filename

    def load_total_model(self):
        try:
            model = joblib.load(self.model_filename)
            return model
        except FileNotFoundError:
            raise FileNotFoundError(f"無法找到模型檔案: {self.model_filename}")
        except Exception as e:
            raise Exception(f"載入模型時發生錯誤: {e}")

    def process_features(self):
        # 計算 day_of_year 和 weekday
        date = pd.to_datetime(self.date_string)
        day_of_year = date.timetuple().tm_yday
        weekday = date.weekday()  # 0 = Monday, 6 = Sunday

        # 取得所有可能的飲料組合（從訓練資料來）
        df = pd.read_csv(self.csv_filename)
        # 確保類別型變數
        for col in ["drink_name", "ice", "weather_status"]:
            df[col] = df[col].astype("category")
        # 取得所有飲料種類
        drink_combinations = df[["drink_name", "ice"]].drop_duplicates()
        # 建立預測 DataFrame
        predict_df = drink_combinations.copy()
        predict_df["weather_status"] = self.weather
        predict_df["weather_temperature"] = self.temperature
        predict_df["day_of_year"] = day_of_year
        predict_df["weekday"] = weekday
        predict_df["daily_total_sales"] = self.daily_total_sales
        # 轉換類別型變數
        for col in ["drink_name", "ice", "weather_status"]:
            predict_df[col] = predict_df[col].astype("category")
        # 特徵欄位
        features = ["drink_name", "ice", "weather_status", "weather_temperature", "day_of_year", "weekday", "daily_total_sales"]
        return predict_df, features

    def pred(self):
        model = self.load_total_model()
        predict_df, features = self.process_features()
        # 預測銷量
        predict_df["predicted_sales"] = model.predict(predict_df[features])
        # 避免負數銷量
        predict_df["predicted_sales"] = predict_df["predicted_sales"].apply(lambda x: max(0, x))
        # # 顯示結果
        # print(predict_df[["drink_name", "ice", "predicted_sales"]])
        # 儲存預測結果
        # predict_df.to_csv("predict/sales_pred", index=False)
        # print("預測完成，結果已存入 predicted_sales_manual.csv")

        return predict_df

    def get_top_6_sales_by_condition(self):
        predict_df = self.pred()
        if self.temperature >= 22:
            filtered_df = predict_df[predict_df['ice'] != 'hot']
        else:
            filtered_df = predict_df[predict_df['ice'] == 'hot']

        grouped_sales = filtered_df.groupby('drink_name', observed=False)['predicted_sales'].sum()
        # top_3 = grouped_sales.sort_values(ascending=False).head(3)
        # top_4_to_6 = grouped_sales.sort_values(ascending=False).iloc[3:6]
        top_6 = grouped_sales.sort_values(ascending=False).iloc[:6]
        return list(top_6.index)


