import os

# total_model_filename = "sales_total_model_v2_2025_03_18.pkl"
# sales_model_filename = "lgbm_drink_weather_model_v4_2025_03_18.pkl"
# sales_csv_filename = "drink_orders_2025_03_18.csv"

class LoadPath:
    def __init__(self, total_model_filename, sales_model_filename, sales_csv_filename):
        self.total_model_filename = total_model_filename
        self.sales_model_filename = sales_model_filename
        self.sales_csv_filename = sales_csv_filename

    def load_total_model_path(self):
        # 取得當前檔案所在資料夾的絕對路徑
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        model_path = os.path.join(base_dir, "predict", "total_pred", self.total_model_filename)
        # 確保模型檔案存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型檔案不存在: {model_path}")

        return model_path
        # 載入模型
        # model = joblib.load(model_path)
        # return model

    def load_sales_model_path(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        model_path = os.path.join(base_dir, "predict", "sales_pred", self.sales_model_filename)
        # 確保模型檔案存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型檔案不存在: {model_path}")

        return model_path
        # 載入模型
        # model = joblib.load(model_path)
        # return model

    def load_sales_csv_path(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        csv_path = os.path.join(base_dir, "predict", "new_data", self.sales_csv_filename)
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"csv檔案不存在: {csv_path}")

        return csv_path      
        # df = pd.read_csv(csv_path)
        # return df
