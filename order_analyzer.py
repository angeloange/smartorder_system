from openai import OpenAI
import os

class OrderAnalyzer:
    def __init__(self):
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            print(f"初始化 OpenAI 客戶端時發生錯誤：{str(e)}")
            raise

    def analyze_order(self, text):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個飲料點餐助手。請從顧客的訂單中提取：飲料名稱、容量大小、冰塊、糖度。"},
                    {"role": "user", "content": text}
                ]
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            print(f"分析訂單時發生錯誤：{str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _parse_response(self, response):
        # 簡單的回應範例
        return [{
            'drink_name': '綠茶',
            'size': '大杯',
            'ice': 'normal',
            'sugar': 'half'
        }]