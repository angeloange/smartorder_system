from openai import OpenAI
import json

class OrderAnalyzer:
    def __init__(self):
        self.client = OpenAI()  # 確保環境變數中有 OPENAI_API_KEY
        self.menu = ["珍珠奶茶", "紅茶", "綠茶", "奶茶", "青茶"]

    def analyze_order(self, text):
        try:
            # 系統提示詞
            system_prompt = """你是一位飲料店的點餐人員，請分析客人的點餐需求並回傳 JSON 格式的訂單內容。
            規則：
            1. sugar只能是(全糖,半糖,無糖)
            2. ice只能是(正常冰,少冰,微冰,去冰,熱)
            3. size只能是(大杯,小杯)
            4. drink_name只能是菜單中的品項
            
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

            # 呼叫 OpenAI API
            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            
            result = completion.choices[0].message.content
            print(f"API 回應: {result}")  # 新增除錯訊息
            
            # 確保回應是有效的 JSON
            return json.loads(result)
            
        except Exception as e:
            print(f"OpenAI API 錯誤: {str(e)}")  # 新增除錯訊息
            return {
                "status": "error",
                "message": f"分析訂單時發生錯誤: {str(e)}"
            }