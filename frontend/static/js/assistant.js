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
            
            // 如果是助手訊息，使用語音播放 - 嘗試多種方式調用
            if (type === 'assistant') {
                // 獲取純文本（去除HTML標記）
                const plainText = text.replace(/<[^>]*>/g, '');
                
                // 請求強制播放語音
                console.log('請求播放語音:', plainText);
                
                // 方法1: 使用全局 voiceManager
                if (window.voiceManager && typeof window.voiceManager.speak === 'function') {
                    console.log('使用 window.voiceManager 播放');
                    window.voiceManager.speak(plainText);
                }
                
                // 添加語音指示器
                messageEl.classList.add('speaking');
            }
            
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
                
                // 擴展確認關鍵詞列表，增加更多常用表達
                const confirmKeywords = ['確認', '好', '好的', '行', '是', '沒問題', '可以', 
                                       '對', '要', '正確', '確定', '訂購', '下單', '可', '嗯'];
                const cancelKeywords = ['取消', '不要', '不', '算了', '錯', '否', '不對'];
                
                // 更智能的確認判斷
                const hasConfirmKeyword = confirmKeywords.some(keyword => text.includes(keyword));
                const hasCancelKeyword = cancelKeywords.some(keyword => text.includes(keyword));
                
                console.log('檢測到訂單確認對話，判斷結果：', { hasConfirmKeyword, hasCancelKeyword });
                
                if (hasConfirmKeyword && !hasCancelKeyword) {
                    // 直接確認訂單，不發送文字到後端分析
                    console.log('用戶確認訂單，直接處理確認流程');
                    
                    // 禁用輸入框，防止重複操作
                    chatInput.disabled = true;
                    
                    if (window.orderCore && typeof window.orderCore.confirmOrder === 'function') {
                        window.orderCore.confirmOrder()
                            .then(result => {
                                console.log('訂單確認結果:', result);
                                // 重新啟用輸入框
                                chatInput.disabled = false;
                                
                                if (result.success) {
                                    // 格式化訂單號碼顯示
                                    let orderNumber = result.orderNumber || '';
                                    if (typeof orderNumber === 'string' && orderNumber.startsWith('[')) {
                                        try {
                                            orderNumber = JSON.parse(orderNumber)[0] || orderNumber;
                                        } catch (e) {
                                            orderNumber = orderNumber.replace(/[\[\]']/g, '');
                                        }
                                    }
                                    
                                    const orderMessage = `訂單已確認！您的取餐號碼是 ${orderNumber}，謝謝您的光臨。`;
                                    
                                    // 添加到聊天界面
                                    this.addMessage('assistant', orderMessage);
                                    
                                    // 使用SweetAlert顯示取餐號碼
                                    if (typeof Swal !== 'undefined') {
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
                                    }
                                } else {
                                    this.addMessage('assistant', result.message || '訂單確認失敗，請稍後再試。');
                                }
                            })
                            .catch(err => {
                                console.error('確認訂單出錯:', err);
                                chatInput.disabled = false;
                                this.addMessage('assistant', '處理訂單時出現錯誤，請稍後再試。');
                            });
                        
                        // 重要：不再處理後續文字輸入
                        return;
                    }
                } else if (hasCancelKeyword) {
                    // 取消訂單處理...
                    // 現有代碼維持不變
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


        // ===== 語音輸入功能 =====
    let recognition = null;
    let isListening = false;
    let resultIndicator = null;

    // 切換語音輸入功能
    function toggleVoiceInput() {
        if (isListening) {
            stopVoiceInput();
        } else {
            startVoiceInput();
        }
    }

    // 啟動語音輸入
    function startVoiceInput() {
        try {
            console.log('開始語音輸入');
            
            // 檢查瀏覽器支持
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert('您的瀏覽器不支持語音識別，請使用Chrome或Edge等現代瀏覽器');
                return;
            }
            
            // 更新按鈕樣式
            const voiceBtn = document.getElementById('chatVoiceBtn');
            if (voiceBtn) {
                voiceBtn.classList.add('recording');
            }
            
            // 顯示錄音指示器
            const chatMessages = document.getElementById('chatMessages');
            const feedbackMsg = document.createElement('div');
            feedbackMsg.id = 'recordingIndicator';
            feedbackMsg.className = 'message system recording-indicator';
            feedbackMsg.innerHTML = '<div class="recording-dot"></div> 正在聆聽您的聲音...';
            
            if (chatMessages) {
                chatMessages.appendChild(feedbackMsg);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // 創建語音識別結果顯示區
            resultIndicator = document.createElement('div');
            resultIndicator.id = 'speechResult';
            resultIndicator.className = 'message system speech-result';
            resultIndicator.textContent = '等待您說話...';
            
            if (chatMessages) {
                chatMessages.appendChild(resultIndicator);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // 初始化語音識別
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'zh-TW';
            recognition.interimResults = true;
            recognition.continuous = true;
            
            // 處理結果
            // 修改語音識別結果處理部分（約在第620行附近）
            recognition.onresult = function(event) {
                let interimTranscript = '';
                let finalTranscript = '';
                
                // 提取識別結果
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                // 顯示中間結果
                if (interimTranscript !== '') {
                    if (resultIndicator) {
                        resultIndicator.textContent = interimTranscript;
                        
                        const chatMessages = document.getElementById('chatMessages');
                        if (chatMessages) {
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                    }
                }
                
                // 處理最終結果
                if (finalTranscript !== '') {
                    console.log('識別到語音:', finalTranscript);
                    
                    // 移除中間結果顯示，讓用戶訊息顯示得更自然
                    if (resultIndicator && resultIndicator.parentNode) {
                        resultIndicator.parentNode.removeChild(resultIndicator);
                        resultIndicator = null;
                    }
                    
                    // 關鍵修改：不在這裡添加用戶訊息，而是通過 handleUserInput 添加
                    // 使用 chatInput 進行處理，這樣會統一走相同的流程
                    const chatInput = document.getElementById('chatInput');
                    if (chatInput) {
                        // 設置輸入值
                        chatInput.value = finalTranscript;
                        // 使用標準處理邏輯，這會添加用戶訊息並處理
                        assistant.handleUserInput();
                        // 清空輸入框
                        chatInput.value = '';
                    } else {
                        // 備用方案：如果找不到輸入框，直接添加訊息和處理
                        assistant.addMessage('user', finalTranscript);
                        assistant.processChat(finalTranscript);
                    }
                    
                    // 重新創建結果顯示區，為下一輪識別做準備
                    const chatMessages = document.getElementById('chatMessages');
                    if (chatMessages) {
                        resultIndicator = document.createElement('div');
                        resultIndicator.id = 'speechResult';
                        resultIndicator.className = 'message system speech-result';
                        resultIndicator.textContent = '等待您說話...';
                        chatMessages.appendChild(resultIndicator);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }
                }
            };
            // 錯誤處理
            recognition.onerror = function(event) {
                console.error('語音識別錯誤:', event.error);
                
                if (event.error === 'not-allowed') {
                    alert('無法訪問麥克風，請確保您已授予網站麥克風權限');
                    stopVoiceInput();
                }
            };
            
            // 開始識別
            recognition.start();
            isListening = true;
            
        } catch (error) {
            console.error('啟動語音識別錯誤:', error);
            alert('啟動語音識別時出錯：' + error.message);
            
            // 確保重置狀態
            stopVoiceInput();
        }
    }

    // 停止語音輸入
    function stopVoiceInput() {
        console.log('停止語音輸入');
        
        // 移除按鈕樣式
        const voiceBtn = document.getElementById('chatVoiceBtn');
        if (voiceBtn) {
            voiceBtn.classList.remove('recording');
        }
        
        // 移除錄音指示器
        const indicator = document.getElementById('recordingIndicator');
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
        
        // 移除結果顯示
        if (resultIndicator && resultIndicator.parentNode) {
            resultIndicator.parentNode.removeChild(resultIndicator);
            resultIndicator = null;
        }
        
        // 停止語音識別
        if (recognition) {
            try {
                recognition.stop();
            } catch (e) {
                console.log('停止語音識別時出錯:', e);
            }
            recognition = null;
        }
        
        isListening = false;
    }

    // 自動解鎖音頻，兼容移動設備
    function unlockAudio() {
        try {
            // 創建並播放靜音音頻
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const buffer = audioContext.createBuffer(1, 1, 22050);
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(0);
        } catch (e) {
            console.log('解鎖音頻失敗:', e);
        }
    }

    // 在任何用戶交互時解鎖音頻
    document.addEventListener('click', unlockAudio, { once: true });
    document.addEventListener('touchstart', unlockAudio, { once: true });




    
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
        
        // 綁定麥克風按鈕
        const chatVoiceBtn = document.getElementById('chatVoiceBtn');
        if (chatVoiceBtn) {
            console.log('找到聊天語音按鈕，添加點擊事件');
            
            chatVoiceBtn.addEventListener('click', function() {
                console.log('聊天語音按鈕被點擊');
                toggleVoiceInput();
            });
        }

        // 添加語音聽寫樣式
        const voiceStyle = document.createElement('style');
        voiceStyle.textContent = `
            #chatVoiceBtn.recording {
                color: #f44336;
                animation: pulse 1s infinite;
            }
            
            .recording-indicator {
                display: flex;
                align-items: center;
                background-color: #f1f1f1;
                padding: 8px 12px;
                border-radius: 8px;
                margin-bottom: 10px;
                color: #555;
                font-style: italic;
            }
            
            .recording-dot {
                width: 12px;
                height: 12px;
                background-color: #f44336;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 1s infinite;
            }
            
            .speech-result {
                font-style: italic;
                color: #666;
                background-color: #f9f9f9;
                padding: 4px 8px;
                border-radius: 4px;
                margin-bottom: 10px;
            }
        `;
        document.head.appendChild(voiceStyle);
        
        // 添加語音指示器樣式
        const style = document.createElement('style');
        style.textContent = `
            .message.assistant.speaking {
                position: relative;
            }
            .message.assistant.speaking::after {
                content: '';
                position: absolute;
                right: 10px;
                top: 10px;
                width: 8px;
                height: 8px;
                background-color: #4CAF50;
                border-radius: 50%;
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.5; transform: scale(1.2); }
                100% { opacity: 1; transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
        
        // 註冊語音管理器回調函數
        if (window.voiceManager && typeof window.voiceManager.registerCallbacks === 'function') {
            window.voiceManager.registerCallbacks({
                onSpeakStart: function() {
                    // 語音開始時的視覺效果
                    const chatAssistant = document.querySelector('.chat-assistant');
                    if (chatAssistant) {
                        chatAssistant.classList.add('speaking');
                    }
                },
                onSpeakEnd: function() {
                    // 語音結束時的視覺效果
                    const chatAssistant = document.querySelector('.chat-assistant');
                    if (chatAssistant) {
                        chatAssistant.classList.remove('speaking');
                    }
                    
                    // 移除訊息的說話指示器
                    const speakingMessage = document.querySelector('.message.assistant.speaking');
                    if (speakingMessage) {
                        speakingMessage.classList.remove('speaking');
                    }
                }
            });
        }
        
        // 初始化聲音解鎖（解決移動設備上的問題）
        function unlockAudio() {
            // 創建並播放一個靜音的音頻
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const buffer = audioContext.createBuffer(1, 1, 22050);
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(0);
            
            // 使用 Web Speech API 解鎖
            if (window.speechSynthesis) {
                const utterance = new SpeechSynthesisUtterance('');
                utterance.volume = 0;
                window.speechSynthesis.speak(utterance);
            }
        }
        
        // 在用戶首次點擊時解鎖音頻
        document.addEventListener('click', function audioUnlock() {
            unlockAudio();
            document.removeEventListener('click', audioUnlock);
        }, { once: true });
        
        // 添加歡迎訊息
        setTimeout(function() {
            assistant.addMessage('assistant', '歡迎光臨！我是您的飲料助手。請問您今天想喝什麼呢？');
        }, 500);
    });
    
    console.log('非模塊版助手已初始化');
})();