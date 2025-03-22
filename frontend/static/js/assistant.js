/**
 * 助手腳本 - 用於初始化和配置虛擬助手
 * 這是一個非模塊腳本，可直接在瀏覽器中執行
 */

(function() {
    // 確保不重複初始化
    if (window.assistant) return;
    
    // 在等待模塊版本的同時，初始化一個簡單版本
    const assistant = {
        state: 'idle',
        
        /**
         * 顯示訊息
         * @param {string} type 訊息類型 (user, assistant)
         * @param {string} text 訊息內容
         */
        addMessage: function(type, text) {
            console.log(`[簡易版助手] 添加${type}訊息:`, text);
            
            const chatMessages = document.getElementById('chatMessages');
            if (!chatMessages) return;
            
            // 創建消息元素
            const messageEl = document.createElement('div');
            messageEl.className = `message ${type}`;
            
            // 檢查是否為訂單確認訊息
            const isOrderConfirmation = type === 'assistant' && 
                                     text.includes('確認一下訂單') && 
                                     text.includes('請問確認');
            
            if (isOrderConfirmation) {
                messageEl.classList.add('order-confirmation');
            }
            
            // 訊息內容
            messageEl.textContent = text;
            
            // 如果是訂單確認，添加按鈕
            if (isOrderConfirmation && window.orderCore) {
                const buttonsDiv = document.createElement('div');
                buttonsDiv.className = 'confirm-buttons';
                
                // 確認按鈕
                const confirmBtn = document.createElement('button');
                confirmBtn.className = 'confirm-btn';
                confirmBtn.textContent = '確認訂單';
                confirmBtn.onclick = async function() {
                    if (window.orderCore && typeof window.orderCore.confirmOrder === 'function') {
                        const result = await window.orderCore.confirmOrder();
                        if (result.success) {
                            assistant.addMessage('assistant', result.message);
                        } else {
                            assistant.addMessage('assistant', result.message || '訂單確認失敗');
                        }
                    } else {
                        assistant.addMessage('assistant', '訂單系統尚未就緒，請稍後再試');
                    }
                };
                
                // 取消按鈕
                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'cancel-btn';
                cancelBtn.textContent = '取消訂單';
                cancelBtn.onclick = function() {
                    if (window.orderCore && typeof window.orderCore.cancelOrder === 'function') {
                        const message = window.orderCore.cancelOrder();
                        assistant.addMessage('assistant', message);
                    } else {
                        assistant.addMessage('assistant', '訂單已取消');
                    }
                };
                
                buttonsDiv.appendChild(confirmBtn);
                buttonsDiv.appendChild(cancelBtn);
                messageEl.appendChild(buttonsDiv);
            }
            
            // 添加到聊天容器
            chatMessages.appendChild(messageEl);
            
            // 滾動到底部
            chatMessages.scrollTop = chatMessages.scrollHeight;
        },
        
        /**
         * 處理用戶輸入
         */
        handleUserInput: function() {
            const chatInput = document.getElementById('chatInput');
            if (!chatInput) return;
            
            const text = chatInput.value.trim();
            if (!text) return;
            
            chatInput.value = '';
            
            // 添加用戶訊息
            this.addMessage('user', text);
            
            // 檢查是否有待確認的訂單
            if (window.orderCore && 
                window.orderCore.getOrderState && 
                window.orderCore.getOrderState().hasActiveOrder && 
                window.orderCore.getOrderState().state === 'confirming') {
                
                // 使用確認關鍵詞簡單判斷
                const confirmKeywords = ['確認', '好', '是', '沒問題', '可以', '對', '要', '正確'];
                const cancelKeywords = ['取消', '不要', '不', '算了', '錯'];
                
                const isConfirm = confirmKeywords.some(keyword => text.includes(keyword));
                const isCancel = cancelKeywords.some(keyword => text.includes(keyword));
                
                if (isConfirm && !isCancel) {
                    // 確認訂單
                    console.log('用戶確認訂單');
                    if (window.orderCore && typeof window.orderCore.confirmOrder === 'function') {
                        window.orderCore.confirmOrder().then(result => {
                            this.addMessage('assistant', result.message);
                        });
                    } else {
                        this.addMessage('assistant', '訂單系統尚未就緒，請稍後再試');
                    }
                    return;
                } else if (isCancel) {
                    // 取消訂單
                    console.log('用戶取消訂單');
                    if (window.orderCore && typeof window.orderCore.cancelOrder === 'function') {
                        const message = window.orderCore.cancelOrder();
                        this.addMessage('assistant', message);
                    } else {
                        this.addMessage('assistant', '訂單已取消');
                    }
                    return;
                }
            }
            
            // 一般對話處理
            this.processChat(text);
        },
        
        /**
         * 處理聊天
         * @param {string} text 用戶輸入
         */
        processChat: async function(text) {
            try {
                this.setState('thinking');
                
                // 檢查是否直接是點餐
                const isDrinkOrder = this.detectDrinkOrder(text);
                if (isDrinkOrder) {
                    console.log('檢測到直接點餐，使用訂單分析器');
                    this.processOrderInput(text);
                    return;
                }
                
                // 發送到後端聊天分析
                const response = await fetch('/analyze_chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                
                const result = await response.json();
                
                // 檢查是否為訂單意圖
                if (result.is_order === true) {
                    console.log('檢測到點餐意圖');
                    
                    if (result.order_details && result.order_details.length > 0) {
                        console.log('有訂單詳情，設置訂單');
                        
                        // 保存訂單到orderCore
                        if (window.orderCore) {
                            window.orderCore.currentOrder = result.order_details;
                            window.orderCore.state = 'confirming';
                        }
                        
                        // 顯示確認消息
                        this.addMessage('assistant', result.reply);
                    } else {
                        // 有意圖但無詳情
                        this.addMessage('assistant', result.reply);
                    }
                } else {
                    // 一般聊天
                    if (result.reply) {
                        this.addMessage('assistant', result.reply);
                    } else {
                        this.addMessage('assistant', '抱歉，我不太理解您的意思。請問您想喝什麼飲料呢？');
                    }
                }
            } catch (error) {
                console.error('處理聊天時出錯:', error);
                this.addMessage('assistant', '抱歉，系統暫時遇到問題，請稍後再試。');
            } finally {
                this.setState('idle');
            }
        },
        
        /**
         * 設置助手狀態
         * @param {string} emotion 表情
         */
        setState: function(emotion) {
            this.state = emotion;
            console.log('設置表情:', emotion);
            
            // 根據需要控制表情等
        },
        
        /**
         * 檢測是否直接是飲料訂單
         * @param {string} text 用戶輸入
         * @return {boolean} 是否為飲料訂單
         */
        detectDrinkOrder: function(text) {
            // 簡單的飲料名稱列表
            const drinks = [
                '珍珠奶茶', '紅茶', '綠茶', '奶茶', '青茶', '烏龍茶', 
                '冬瓜茶', '檸檬茶', '蜂蜜檸檬', '梅子綠茶'
            ];
            
            // 如果是單獨一個飲料名稱
            if (drinks.includes(text.trim())) {
                return true;
            }
            
            // 飲料特徵詞
            const drinkKeywords = ['杯', '茶', '咖啡', '奶茶', '拿鐵'];
            const hasKeyword = drinkKeywords.some(keyword => text.includes(keyword));
            
            // 訂購特徵詞
            const orderKeywords = ['要', '來', '點', '買', '訂', '喝'];
            const hasOrderWord = orderKeywords.some(keyword => text.includes(keyword));
            
            // 規格特徵詞
            const specKeywords = ['大杯', '中杯', '小杯', '熱', '冰', '溫', '糖'];
            const hasSpec = specKeywords.some(keyword => text.includes(keyword));
            
            return hasKeyword && (hasOrderWord || hasSpec);
        },
        
        /**
         * 處理訂單輸入
         * @param {string} text 訂單文本
         */
        processOrderInput: async function(text) {
            console.log('開始處理訂單輸入:', text);
            
            try {
                // 發送到訂單分析器
                const response = await fetch('/analyze_text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                
                const result = await response.json();
                console.log('訂單分析結果:', result);
                
                if (result.status === 'success' && result.order_details) {
                    // 保存訂單到orderCore
                    if (window.orderCore) {
                        window.orderCore.currentOrder = result.order_details;
                        window.orderCore.state = 'confirming';
                    }
                    
                    // 建立訂單確認訊息
                    this.showOrderConfirmation(result.order_details);
                } else {
                    // 分析失敗
                    this.addMessage('assistant', result.message || '抱歉，我無法理解您的訂單。請提供更多細節，如飲料名稱、大小、甜度和冰量。');
                }
            } catch (error) {
                console.error('處理訂單時出錯:', error);
                this.addMessage('assistant', '抱歉，訂單處理系統出現問題，請稍後再試。');
            } finally {
                this.setState('idle');
            }
        },
        
        /**
         * 顯示訂單確認
         * @param {Array} orderDetails 訂單詳情
         * @param {string} orderText 可選的格式化訂單文本
         */
        showOrderConfirmation: function(orderDetails, orderText) {
            if (!orderDetails || !Array.isArray(orderDetails)) return;
            
            // 格式化訂單詳情
            let formattedText = orderText;
            if (!formattedText) {
                formattedText = this.formatOrderText(orderDetails);
            }
            
            // 顯示確認訊息
            this.addMessage('assistant', `我幫您確認一下訂單：${formattedText}\n\n請問確認訂購嗎？`);
        },
        
        /**
         * 格式化訂單文本
         * @param {Array} orderDetails 訂單詳情
         * @return {string} 格式化的訂單文本
         */
        formatOrderText: function(orderDetails) {
            if (!orderDetails || !Array.isArray(orderDetails)) return "";
            
            return orderDetails.map(item => {
                const parts = [];
                if (item.size) parts.push(item.size);
                if (item.sugar) parts.push(item.sugar);
                if (item.ice) parts.push(item.ice);
                parts.push(item.drink_name);
                
                let orderText = parts.join('');
                if (item.quantity > 1) {
                    orderText += ` ${item.quantity}杯`;
                }
                return orderText;
            }).join('、');
        }
    };
    
    // 設置全局訪問
    window.assistant = assistant;
    
    // 在DOM加載完成後綁定事件
    document.addEventListener('DOMContentLoaded', function() {
        // 綁定發送按鈕
        const sendBtn = document.getElementById('chatSendBtn');
        if (sendBtn) {
            sendBtn.addEventListener('click', function() {
                assistant.handleUserInput();
            });
        }
        
        // 綁定輸入框回車事件
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    assistant.handleUserInput();
                }
            });
        }
        
        // 添加歡迎訊息
        setTimeout(function() {
            assistant.addMessage('assistant', '歡迎光臨！我是您的飲料助手。請問您今天想喝什麼呢？');
        }, 500);
    });
    
    console.log('非模塊版助手已初始化');
})();