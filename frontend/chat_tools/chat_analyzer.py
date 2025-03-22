from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import logging

class ChatAnalyzer:
    def __init__(self):
        # 載入環境變數
        load_dotenv()
        
        # 確保有 API 金鑰
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未設置 OPENAI_API_KEY 環境變數")
            
        self.client = OpenAI(
            api_key=api_key
        )
        
        # 用於儲存對話歷史
        self.conversation_history = []
        
        # 初始化日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('chat_analyzer')
    
    def analyze_chat(self, text, conversation_history=None):
        """分析聊天內容，返回適當的回應和意圖"""
        try:
            # 使用提供的歷史記錄或內部歷史記錄
            history = conversation_history if conversation_history else self.conversation_history
            
            # 構建詳細的系統提示，幫助 GPT 更準確識別點餐意圖
            system_prompt = """你是一個智慧點餐助手，位於飲料店內。你的主要目標是幫助客戶點餐。

當用戶出現下列情況時，請判斷為點餐意圖：
1. 明確提到特定飲料名稱，例如：珍珠奶茶、紅茶、綠茶等
2. 使用點餐相關詞彙，例如：我要、我想喝、來一杯、點、訂購等
3. 談論甜度或冰量，例如：半糖、少冰、無糖等
4. 詢問菜單或推薦飲料時
5. 表明想要購買或訂購的意願

請以 JSON 格式回應，包含以下字段：
{
    "reply": "對用戶的友善回覆",
    "intent": "chat 或 order",
    "confidence": 0.0到1.0之間的數值
}

不要在回覆中提到你是AI或機器人。保持回覆簡短自然，像真人店員一樣。"""
            
            # 構建 messages 序列
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 添加歷史對話，最多10輪
            for msg in history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 添加當前用戶訊息
            messages.append({"role": "user", "content": text})
            
            # 調用 API
            self.logger.info(f"發送對話分析請求: {text}")
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"},
                max_tokens=600
            )
            
            # 分析結果
            result = completion.choices[0].message.content.strip()
            self.logger.info(f"API 回應: {result}")
            
            # 解析 JSON
            response_data = json.loads(result)
            
            # 保存對話歷史
            self.conversation_history.append({"role": "user", "content": text})
            self.conversation_history.append({"role": "assistant", "content": response_data.get("reply", "")})
            
            # 如果歷史太長，移除最舊的對話
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # 標準化回應
            return {
                "status": "success",
                "reply": response_data.get("reply", "我不太明白您的意思，能請您再說一次嗎？"),
                "intent": response_data.get("intent", "chat"),
                "confidence": response_data.get("confidence", 0.5),
                "is_order_intent": response_data.get("intent", "") == "order"
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI API 錯誤: {str(e)}")
            # API 發生錯誤時返回錯誤訊息
            return {
                "status": "error",
                "message": f"分析對話時發生錯誤: {str(e)}",
                "reply": "抱歉，我現在遇到了一些問題，請稍後再試或直接告訴我您想點什麼飲料。",
                "intent": "error"
            }
            
    def reset_conversation(self):
        """重置對話歷史"""
        self.conversation_history = []