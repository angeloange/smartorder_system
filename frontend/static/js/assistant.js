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
            console.log(`[助手] 添加${type}訊息:`, text);
            
            const chatMessages = document.getElementById('chatMessages');
            if (!chatMessages) return;
            
            // 創建消息元素
            const messageEl = document.createElement('div');
            messageEl.className = `message ${type}`;
            
            // 檢查是否為訂單確認訊息
            const isOrderConfirmation = type === 'assistant' && 
                                     text.includes('確認一下訂單') && 
                                     text.includes('請問確認');
            
            const isOrderCompleted = type === 'assistant' && text.includes('訂單已確認') && text.includes('取餐號碼');
            
            if (isOrderConfirmation) {
                messageEl.classList.add('order-confirmation');
            }
            
            if (isOrderCompleted) {
                messageEl.classList.add('order-completed');
                
                // 使訂單號碼更醒目
                const orderNumberMatch = text.match(/號碼是\s*(\d+)/);
                if (orderNumberMatch && orderNumberMatch[1]) {
                    const orderNumber = orderNumberMatch[1];
                    
                    // 替換文本中的訂單號為帶樣式的版本
                    text = text.replace(
                        `號碼是 ${orderNumber}`, 
                        `號碼是 <span class="order-number">${orderNumber}</span>`
                    );
                    
                    // 添加樣式
                    const style = document.createElement('style');
                    style.textContent = `
                        .order-number {
                            font-weight: bold;
                            font-size: 1.2em;
                            color: #FF5722;
                            background: #FFF3E0;
                            padding: 2px 6px;
                            border-radius: 4px;
                        }
                        .order-completed {
                            background-color: #E8F5E9;
                            border-left: 4px solid #4CAF50;
                        }
                    `;
                    document.head.appendChild(style);
                    
                    // 使用innerHTML而不是textContent
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'message-content';
                    contentDiv.innerHTML = text;
                    messageEl.appendChild(contentDiv);
                    
                    chatMessages.appendChild(messageEl);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    return;
                }
            }
            
            // 正常文本情況
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = text;
            messageEl.appendChild(contentDiv);
            
            // 如果是訂單確認，添加按鈕
            if (isOrderConfirmation && window.orderCore) {
              // 添加確認和取消按鈕容器
                const buttonsDiv = document.createElement('div');
                buttonsDiv.className = 'confirm-buttons';
                
                // 確認按鈕
                const confirmBtn = document.createElement('button');
                confirmBtn.className = 'confirm-btn';
                confirmBtn.textContent = '確認訂單';
                
                // 取消按鈕
                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'cancel-btn';
                cancelBtn.textContent = '取消訂單';
                
                // 添加按鈕到容器
                buttonsDiv.appendChild(confirmBtn);
                buttonsDiv.appendChild(cancelBtn);
                
                // 添加按鈕容器到消息
                messageEl.appendChild(buttonsDiv);
                
                // 確認按鈕點擊處理
                confirmBtn.onclick = async function() {
                    // 立即禁用按鈕，防止重複點擊
                    const btnContainer = this.parentElement;
                    const allButtons = btnContainer.querySelectorAll('button');
                    
                    // 禁用所有按鈕
                    allButtons.forEach(btn => {
                        btn.disabled = true;
                        btn.style.opacity = "0.5";
                        btn.style.cursor = "not-allowed";
                    });
                    
                    // 將按鈕文本改為處理中
                    this.innerHTML = '<span class="spinner"></span> 處理中...';
                    
                    // 添加spinner樣式
                    const style = document.createElement('style');
                    style.textContent = `
                        .spinner {
                            display: inline-block;
                            width: 12px;
                            height: 12px;
                            border: 2px solid rgba(255,255,255,.3);
                            border-radius: 50%;
                            border-top-color: #fff;
                            animation: spin 1s ease-in-out infinite;
                        }
                        @keyframes spin {
                            to { transform: rotate(360deg); }
                        }
                    `;
                    document.head.appendChild(style);
                    
                    try {
                        // 確認訂單
                        if (window.orderCore && typeof window.orderCore.confirmOrder === 'function') {
                            const result = await window.orderCore.confirmOrder();
                            console.log('訂單確認結果:', result);
                            
                            // 移除訂單確認UI
                            const confirmationMessage = this.closest('.message.order-confirmation');
                            if (confirmationMessage) {
                                const buttonsDiv = confirmationMessage.querySelector('.confirm-buttons');
                                if (buttonsDiv) {
                                    buttonsDiv.remove();
                                }
                            }
                            
                            // 處理訂單確認結果
                            if (result.success) {
                                // 處理訂單編號格式
                                let orderNumber = result.orderNumber || '';
                                if (typeof orderNumber === 'string' && orderNumber.startsWith('[')) {
                                    try {
                                        // 嘗試解析JSON格式的訂單號
                                        orderNumber = JSON.parse(orderNumber)[0] || orderNumber;
                                    } catch (e) {
                                        // 失敗時使用原始值但去除方括號
                                        orderNumber = orderNumber.replace(/[\[\]']/g, '');
                                    }
                                }
                                
                                const orderMessage = `訂單已確認！您的取餐號碼是 ${orderNumber}，謝謝您的光臨。`;
                                
                                // 添加到聊天界面，使用特殊格式突出顯示訂單編號
                                assistant.addMessage('assistant', orderMessage);
                                
                                // 使用SweetAlert顯示訂單編號
                                Swal.fire({
                                    title: '訂單已確認',
                                    html: `
                                        <p>好的，尊貴的客人請稍候</p>
                                        <p>正在為您製作飲品</p>
                                        <p>您的取餐號碼是 <strong style="font-size:24px;color:#FF5722">${orderNumber}</strong></p>
                                    `,
                                    icon: 'success',
                                    timer: 5000,
                                    timerProgressBar: true,
                                    showConfirmButton: false
                                });
                            } else {
                                // 訂單確認失敗
                                assistant.addMessage('assistant', result.message || '訂單確認失敗，請稍後再試。');
                            }
                        } else {
                            assistant.addMessage('assistant', '訂單系統未準備好，請稍後再試。');
                        }
                    } catch (error) {
                        console.error('訂單確認出錯:', error);
                        assistant.addMessage('assistant', '處理訂單時出現錯誤，請稍後再試。');
                    }
                };
                
                // 取消按鈕點擊處理
                cancelBtn.onclick = function() {
                    // 立即禁用按鈕，防止重複點擊
                    const btnContainer = this.parentElement;
                    const allButtons = btnContainer.querySelectorAll('button');
                    
                    // 禁用所有按鈕
                    allButtons.forEach(btn => {
                        btn.disabled = true;
                        btn.style.opacity = "0.5";
                        btn.style.cursor = "not-allowed";
                    });
                    
                    // 將按鈕文本改為處理中
                    this.innerHTML = '<span class="spinner"></span> 取消中...';
                    
                    try {
                        // 移除訂單確認UI
                        const confirmationMessage = this.closest('.message.order-confirmation');
                        if (confirmationMessage) {
                            const buttonsDiv = confirmationMessage.querySelector('.confirm-buttons');
                            if (buttonsDiv) {
                                buttonsDiv.remove();
                            }
                        }
                        
                        // 處理訂單取消
                        if (window.orderCore && typeof window.orderCore.cancelOrder === 'function') {
                            const message = window.orderCore.cancelOrder();
                            assistant.addMessage('assistant', message || '訂單已取消，請問您想重新點餐嗎？');
                        } else {
                            assistant.addMessage('assistant', '訂單已取消，請問您想重新點餐嗎？');
                        }
                    } catch (error) {
                        console.error('訂單取消出錯:', error);
                        assistant.addMessage('assistant', '處理訂單取消時出現錯誤，請稍後再試。');
                    }
                };
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
                this.state = 'thinking'; // 直接修改狀態屬性
                
                console.log('處理用戶輸入:', text);
                
                // 所有用戶輸入都交給後端處理
                const response = await fetch('/analyze_chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                });
                
                const result = await response.json();
                console.log('OpenAI 完整回應:', result);
                
                // 根據後端判斷的意圖處理
                if (result.is_order === true) {
                    console.log('OpenAI 檢測到點餐意圖');
                    
                    // 檢查訂單詳情是否存在並有內容
                    if (result.order_details && Array.isArray(result.order_details) && result.order_details.length > 0) {
                        console.log('訂單詳情:', JSON.stringify(result.order_details));
                        
                        // 保存訂單到 orderCore
                        if (window.orderCore) {
                            window.orderCore.currentOrder = result.order_details;
                            window.orderCore.state = 'confirming';
                            
                            // 格式化訂單內容
                            const orderText = this.formatOrderText(result.order_details);
                            // 顯示確認消息
                            this.addMessage('assistant', `我幫您確認一下訂單：${orderText}\n\n請問確認訂購嗎？`);
                        } else {
                            this.addMessage('assistant', '訂單系統暫時無法使用，請稍後再試。');
                        }
                    } else {
                        // 有意圖但無詳情 - 使用API回傳的訊息或顯示默認提示
                        this.addMessage('assistant', result.reply || '請您明確告訴我想要的飲料名稱、大小、甜度和冰量。');
                    }
                } else {
                    // 一般聊天回應
                    this.addMessage('assistant', result.reply || '抱歉，我不太理解您的意思。');
                }
            } catch (error) {
                console.error('處理聊天時出錯:', error);
                this.addMessage('assistant', '抱歉，系統暫時遇到問題，請稍後再試。');
            } finally {
                this.state = 'idle';
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
            const chatAssistant = document.querySelector('.chat-assistant');
            if (chatAssistant) {
                // 移除所有狀態類
                chatAssistant.classList.remove('thinking', 'idle', 'happy', 'confused');
                // 添加新狀態
                chatAssistant.classList.add(emotion);
            }
        },
        /**
         * 檢測是否直接是飲料訂單
         * @param {string} text 用戶輸入
         * @return {boolean} 是否為飲料訂單
         */

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