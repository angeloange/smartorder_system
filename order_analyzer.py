from openai import OpenAI
import json
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class OrderAnalyzer:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("請設定 OPENAI_API_KEY 環境變數")
        self.client = OpenAI(api_key=api_key)
        self.menu = [
            "青茶", "烏龍茶", "紅茶", "綠茶", "檸檬茶", "蜂蜜檸檬", "冬瓜茶", "梅子綠茶",
            "冬瓜檸檬", "普洱茶", "可可", "奶茶", "奶綠", "烏龍奶茶", "焦糖奶茶",
            "波霸奶茶", "椰果奶茶", "蜂蜜奶茶", "仙草奶茶", "布丁奶茶", "巧克力牛奶",
            "美式咖啡", "蜂蜜美式", "卡布奇諾", "焦糖瑪奇朵", "拿鐵咖啡", "摩卡咖啡",
            "烏龍拿鐵", "紅茶咖啡", "牛奶咖啡"
        ]

    def analyze_order(self, text):
        try:
            # 系統提示詞
            system_prompt = f"""你是一位飲料店的點餐人員，請分析客人的點餐需求並回傳 JSON 格式的訂單內容。
            規則：
            1. drink_name必須從以下選項中選擇：{', '.join(self.menu)},如果客人只講了前2個字，請自動補全
            2. sugar必須是: full（全糖）, half（半糖）, free（無糖）,微糖
            3. ice_type必須是: iced（正常冰）, less_ice（少冰）, light_ice（微冰）, no_ice（去冰）, hot（熱）
            4. size必須是: 大杯 或 小杯
            5. 直接回傳JSON格式，不要加入其他文字
            6. 如果客人沒有指定數量，預設為1杯
            7. 如果客人沒有指定冰塊、糖量，預設為正常冰、正常糖
            8. 如果客人使用點餐的text是中文,將其他參數如size,ice_type,sugar_type,quantity都以中文回傳
            回傳格式範例：
            {{
                "drink_name": "綠茶",
                "size": "大杯",
                "ice_type": "正常冰",
                "sugar_type": "半糖",
                "quantity": 1
            }}"""

            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3  # 降低溫度以獲得更一致的回應
            )
            
            result = completion.choices[0].message.content.strip()
            print(f"OpenAI 回應: {result}")
            
            try:
                # 解析 JSON 回應
                order = json.loads(result)
                
                # 確保回應符合資料庫格式
                formatted_order = {
                    'drink_name': order['drink_name'],
                    'size': order['size'],
                    'ice': order['ice_type'],
                    'sugar': order['sugar_type'],
                    'quantity': order.get('quantity', 1)
                }
                
                return [formatted_order]  # 回傳陣列格式
                
            except json.JSONDecodeError as e:
                print(f"JSON 解析錯誤: {e}")
                return {
                    "status": "error",
                    "message": "無法解析訂單格式"
                }
            
        except Exception as e:
            print(f"訂單分析錯誤: {str(e)}")
            return {
                "status": "error",
                "message": f"分析訂單時發生錯誤: {str(e)}"
            }