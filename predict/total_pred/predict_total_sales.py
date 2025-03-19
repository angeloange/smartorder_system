import joblib
import pandas as pd
from predict.models import Pred_total


class Pred_Total_Sales:
    def __init__(self, pred_info: Pred_total):
        self.date_string = pred_info.date_string
        self.weather = pred_info.weather
        self.temperature = pred_info.temperature
        self.model_filename = pred_info.model_filename
        self.weather_mapping = {
                                 "cloudy": 0,
                                 "rainy": 1,
                                 "stormy": 2,
                                 "sunny": 3
                                 }

    def load_total_model(self):
        """load model"""
        try:
            model = joblib.load(self.model_filename)
            return model
        except FileNotFoundError:
            raise FileNotFoundError(f"無法找到模型檔案: {self.model_filename}")
        except Exception as e:
            raise Exception(f"載入模型時發生錯誤: {e}")

    # 處理特徵
    def process_features(self):
        """
        輸入日期 (YYYY-MM-DD)，天氣狀態 (cloudy, rainy, stormy, sunny) 和氣溫
        回傳預測模型所需的 DataFrame
        """
        # 日期轉換
        date = pd.to_datetime(self.date_string)
        weekday = date.weekday()  # 星期幾（0=星期一）
        month = date.month  # 月份
        day_of_year = date.dayofyear  # 一年內的第幾天

        # 天氣轉換
        weather = self.weather.lower()
        if weather not in self.weather_mapping:
            raise ValueError(f"未知的天氣類型: {weather}，請使用 {list(self.weather_mapping.keys())}")

        # 建立 DataFrame
        return pd.DataFrame([{
             "weather_status": self.weather_mapping[weather],
             "weather_temperature": self.temperature,
             "weekday": weekday,
             "month": month,
             "day_of_year": day_of_year
         }])

    def pred(self):
        model = self.load_total_model()

        # 轉換成模型輸入格式
        test_df = self.process_features()

        # 預測銷量
        predicted_sales = model.predict(test_df)

        # 輸出結果
        # print(f"日期: {self.date_string} | 天氣: {self.weather} | 氣溫: {self.temperature}°C")
        # print(f"預測銷量: {predicted_sales[0]:.0f} 杯")

        return round(predicted_sales[0])
