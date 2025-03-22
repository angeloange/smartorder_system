from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import re

class OrderAnalyzer:
    def __init__(self):
        # 載入環境變數
        load_dotenv()
        
        # 確保有 API 金鑰
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("警告: 未設置 OPENAI_API_KEY 環境變數，將使用簡單分析")
            
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        
        # 飲料菜單
        self.drinks_menu = [
            '珍珠奶茶', '紅茶', '綠茶', '奶茶', '青茶', '烏龍茶', '鮮奶茶',
            '冬瓜茶', '檸檬茶', '蜂蜜檸檬', '梅子綠茶', '冬瓜檸檬', '普洱茶',
            '奶綠', '烏龍奶茶', '焦糖奶茶', '波霸奶茶', '椰果奶茶', '蜂蜜奶茶',
            '仙草奶茶', '布丁奶茶', '巧克力牛奶', '美式咖啡', '卡布奇諾', 
            '拿鐵咖啡', '摩卡咖啡', '烏龍拿鐵', '紅茶咖啡', '牛奶咖啡'
        ]
        
        # 杯型
        self.sizes = ['大杯', '中杯', '小杯']
        
        # 冰塊選項
        self.ice_options = ['正常冰', '少冰', '微冰', '去冰', '熱', '溫']
        
        # 甜度選項
        self.sugar_options = ['全糖', '七分糖', '半糖', '三分糖', '微糖', '無糖']
        
        # 數量關鍵詞
        self.quantity_keywords = {
            '一': 1, '二': 2, '兩': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }

    def analyze_order(self, text):
        # 特殊處理：如果文本非常簡短並且是單一飲料名稱
        for drink in self.drinks_menu:
            if text.strip() == drink:
                print(f"處理簡單飲料名稱: {drink}")
                order_detail = {
                    'drink_name': drink,
                    'size': '中杯',  # 默認中杯
                    'ice': '正常冰',  # 默認正常冰
                    'sugar': '全糖',  # 默認全糖
                    'quantity': 1     # 默認1杯
                }
                return [order_detail]
        
        # 修正純飲料名稱可能的輸入格式 "一杯[飲料名]"
        if text.startswith('一杯'):
            for drink in self.drinks_menu:
                if text == f"一杯{drink}":
                    print(f"處理簡單訂單: 一杯{drink}")
                    order_detail = {
                        'drink_name': drink,
                        'size': '中杯',
                        'ice': '正常冰',
                        'sugar': '全糖',
                        'quantity': 1
                    }
                    return [order_detail]
        
        # 檢查是否有 API 金鑰
        if not self.api_key:
            return self.simple_order_analysis(text)
        
        # 使用 OpenAI API 分析訂單
        try:
            # 系統提示詞
            system_prompt = """你是一位飲料店的點餐人員，請分析客人的點餐需求並回傳 JSON 格式的訂單內容。
            規則：
            1. 請分析出飲料名稱、大小、甜度、冰量和數量
            2. sugar只能是(全糖, 半糖, 微糖, 無糖)
            3. ice只能是(正常冰, 少冰, 微冰, 去冰, 熱飲, 溫)
            4. size只能是(大杯, 中杯, 小杯)，預設是中杯
            5. quantity是數量，預設是1
            6. 直接回傳JSON格式，不要加入markdown標記
            
            回傳格式範例：
            [
                {
                    "drink_name": "珍珠奶茶",
                    "size": "大杯",
                    "sugar": "半糖",
                    "ice": "少冰",
                    "quantity": 1
                }
            ]"""

            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            
            result = completion.choices[0].message.content.strip()
            print(f"API 回應: {result}")
            
            # 移除可能的 markdown 標記
            if result.startswith('```'):
                result = result.replace('```json', '').replace('```', '').strip()
            
            return json.loads(result)
            
        except Exception as e:
            print(f"OpenAI API 錯誤: {str(e)}")
            # 如果 API 調用失敗，回退到簡單分析
            return self.simple_order_analysis(text)
    
    def simple_order_analysis(self, text):
        """簡單的訂單分析方法，用於 API 不可用時"""
        try:
            # 嘗試找出飲料名稱
            drink_name = None
            for drink in self.drinks_menu:
                if drink in text:
                    drink_name = drink
                    break
            
            if not drink_name:
                return {
                    'status': 'error',
                    'message': '無法識別飲料名稱，請重新點餐。'
                }
            
            # 尋找甜度
            sugar = '全糖'  # 默認全糖
            for option in self.sugar_options:
                if option in text:
                    sugar = option
                    break
            
            # 尋找冰量
            ice = '正常冰'  # 默認正常冰
            for option in self.ice_options:
                if option in text:
                    ice = option
                    break
            
            # 尋找大小
            size = '中杯'  # 默認中杯
            for option in self.sizes:
                if option in text:
                    size = option
                    break
            
            # 尋找數量
            quantity = 1  # 默認1杯
            for key, value in self.quantity_keywords.items():
                if f"{key}杯" in text:
                    quantity = value
                    break
            
            # 檢查數字
            number_match = re.search(r'(\d+)\s*杯', text)
            if number_match:
                quantity = int(number_match.group(1))
            
            order_detail = {
                'drink_name': drink_name,
                'size': size,
                'ice': ice,
                'sugar': sugar,
                'quantity': quantity
            }
            
            return [order_detail]
            
        except Exception as e:
            print(f"簡單訂單分析錯誤: {str(e)}")
            return {
                'status': 'error',
                'message': '無法識別訂單內容，請提供更多資訊'
            }