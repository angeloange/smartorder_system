from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

class ConversationState(Enum):
    GREETING = "greeting"
    TAKING_ORDER = "taking_order"
    CONFIRMING_ORDER = "confirming_order"
    ASKING_MORE = "asking_more"
    COMPLETING = "completing"

@dataclass
class OrderItem:
    drink_name: str
    size: str = "中杯"
    sugar: str = "正常糖"
    ice: str = "正常冰"

class ChatManager:
    def __init__(self):
        self.state = ConversationState.GREETING
        self.current_order: Dict[str, OrderItem] = {}
        self.last_response = ""
    
    def process_input(self, user_input: str) -> str:
        """處理用戶輸入並返回適當的回應"""
        if self.state == ConversationState.GREETING:
            return self._handle_greeting(user_input)
        elif self.state == ConversationState.TAKING_ORDER:
            return self._handle_order(user_input)
        elif self.state == ConversationState.CONFIRMING_ORDER:
            return self._handle_confirmation(user_input)
        
        return "抱歉，我不太理解。請問您想要點什麼飲料呢？"

    def _handle_greeting(self, user_input: str) -> str:
        self.state = ConversationState.TAKING_ORDER
        return "您好！今天想喝什麼呢？"

    def _handle_order(self, user_input: str) -> str:
        # 這裡後續會整合現有的訂單分析邏輯
        # 暫時返回測試回應
        self.state = ConversationState.CONFIRMING_ORDER
        return "好的，您是否要確認訂單呢？"

    def _handle_confirmation(self, user_input: str) -> str:
        if "是" in user_input or "好" in user_input:
            self.state = ConversationState.COMPLETING
            return "訂單已確認，請稍候"
        else:
            self.state = ConversationState.TAKING_ORDER
            return "好的，請重新告訴我您想要的飲料"