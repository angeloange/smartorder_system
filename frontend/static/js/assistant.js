class VirtualAssistant {
    constructor() {
        this.messages = [];
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.chatSendBtn = document.getElementById('chatSendBtn');
        this.orderConfirmed = false;
        this.currentOrder = null;
        this.initializeAssistant();
    }

    initializeAssistant() {
        // 添加歡迎訊息
        this.addMessage('assistant', '您好！我是您的智慧點餐助手。請問您今天想喝什麼呢？');
        
        // 綁定發送按鈕事件
        this.chatSendBtn.addEventListener('click', () => this.handleUserInput());
        
        // 綁定輸入框按 Enter 事件
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleUserInput();
            }
        });
    }

    async handleUserInput() {
        const input = this.chatInput.value.trim();
        if (!input) return;

        // 顯示用戶輸入
        this.addMessage('user', input);
        this.chatInput.value = '';

        if (this.currentOrder && !this.orderConfirmed) {
            // 處理訂單確認
            if (input.includes('確認') || input.includes('好')) {
                await this.confirmOrder();
            } else if (input.includes('取消') || input.includes('不')) {
                this.cancelOrder();
            } else {
                this.addMessage('assistant', '請告訴我要確認還是取消訂單？');
            }
        } else {
            // 處理新訂單
            await this.processOrder(input);
        }
    }

    async processOrder(input) {
        try {
            const response = await fetch('/analyze_text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: input })
            });

            const result = await response.json();
            if (result.status === 'success') {
                this.currentOrder = result.order_details;
                this.orderConfirmed = false;
                
                const orderText = result.order_details.map(item => 
                    `${item.size}${item.ice}${item.sugar}${item.drink_name}`
                ).join('、');
                
                this.addMessage('assistant', `我幫您確認一下訂單：${orderText}\n請問確認訂購嗎？`);
            } else {
                this.addMessage('assistant', '抱歉，我沒有聽懂您的需求，請您再說一次。');
            }
        } catch (error) {
            console.error('處理訂單時發生錯誤:', error);
            this.addMessage('assistant', '抱歉，系統處理時發生錯誤，請稍後再試。');
        }
    }

    async confirmOrder() {
        try {
            const response = await fetch('/confirm_order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_details: this.currentOrder })
            });

            const result = await response.json();
            if (result.status === 'success') {
                this.addMessage('assistant', `訂單已確認！您的取餐號碼是 ${result.order_number}，請稍候片刻。`);
                this.orderConfirmed = true;
                this.currentOrder = null;
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            this.addMessage('assistant', '抱歉，訂單確認失敗，請稍後再試。');
        }
    }

    cancelOrder() {
        this.currentOrder = null;
        this.orderConfirmed = false;
        this.addMessage('assistant', '好的，已取消訂單。請問您想重新點餐嗎？');
    }

    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}