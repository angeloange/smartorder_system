from openai import OpenAI
import os
from dotenv import load_dotenv
import json

class OrderAnalyzer:
    def __init__(self):
        # 載入環境變數
        load_dotenv()
        
        # 確保有 API 金鑰
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("未設置 OPENAI_API_KEY 環境變數")
            
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.menu = ["珍珠奶茶", "紅茶", "綠茶", "奶茶", "青茶"]

    def analyze_order(self, text):
        try:
            system_prompt = """你是一位飲料店的點餐人員，請分析客人的點餐需求並回傳 JSON 格式的訂單內容。
            規則：
            1. sugar只能是(全糖,少糖,半糖,微糖, 無糖)
            2. ice只能是(正常冰, 少冰, 微冰, 去冰, 熱飲, 常溫)
            3. size只能是(大杯,小杯)
            4. drink_name只能是菜單中的品項
            5. 直接回傳JSON格式，不要加入markdown標記
            
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
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]
            
            return json.loads(result.strip())
            
        except Exception as e:
            print(f"OpenAI API 錯誤: {str(e)}")
            return {
                "status": "error",
                "message": f"分析訂單時發生錯誤: {str(e)}"
            }