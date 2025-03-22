/**
 * 助手核心 - 整合語音、訂單、對話功能
 */
import orderCore from './orderCore.js';
import voiceManager from './voiceManager.js';

class AssistantCore {
    constructor() {
        console.log('初始化助手核心...');
        
        // 初始化界面元素
        this.initUIElements();
        
        // 初始化語音管理器回調
        this.initVoiceManager();
        
        // 訂單核心回調
        this.initOrderCore();
        
        // 添加事件監聽器
        this.initEventListeners();
        
        // 設置初始狀態
        this.state = 'idle'; // idle, listening, speaking, thinking
        
        // 歡迎消息
        setTimeout(() => {
            this.addMessage('assistant', '您好！我是您的智慧點餐助手。請問您今天想喝什麼呢？或是需要我為您推薦飲品？');
        }, 1000);
    }
    
    /**
     * 初始化界面元素
     */
    initUIElements() {
        // 聊天容器
        this.chatMessages = document.getElementById('chatMessages');
        if (!this.chatMessages) {
            console.error('找不到聊天消息容器 #chatMessages');
        }
        
        // 輸入框
        this.chatInput = document.getElementById('chatInput');
        if (!this.chatInput) {
            console.error('找不到聊天輸入框 #chatInput');
        }
        
        // 發送按鈕
        this.chatSendBtn = document.getElementById('chatSendBtn');
        if (!this.chatSendBtn) {
            console.error('找不到發送按鈕 #chatSendBtn');
        }
        
        // 語音按鈕
        this.voiceInputBtn = document.getElementById('chatVoiceBtn');
        if (!this.voiceInputBtn) {
            console.error('找不到語音按鈕 #chatVoiceBtn');
        }
        
        // 訂單信息顯示
        this.numberDisplay = document.querySelector('.number-display');
        this.waitingTimeDisplay = document.querySelector('.waiting-time');
    }
    
    /**
     * 初始化語音管理器
     */
    initVoiceManager() {
        voiceManager.registerCallbacks({
            onSpeakStart: () => {
                console.log('語音開始');
                this.setState('speaking');
            },
            onSpeakEnd: () => {
                console.log('語音結束');
                this.setState('idle');
            },
            onSpeechStart: () => {
                console.log('語音識別開始');
                this.setState('listening');
                if (this.voiceInputBtn) {
                    this.voiceInputBtn.classList.add('recording');
                }
            },
            onSpeechEnd: () => {
                console.log('語音識別結束');
                if (this.voiceInputBtn) {
                    this.voiceInputBtn.classList.remove('recording');
                }
            },
            onSpeechResult: (result) => {
                console.log('語音識別結果:', result);
                if (this.chatInput) {
                    this.chatInput.value = result;
                    this.handleUserInput();
                }
            },
            onSpeechError: (error) => {
                console.error('語音識別錯誤:', error);
                this.setState('idle');
                
                if (error === 'timeout' || error === 'no_speech') {
                    this.addMessage('assistant', '我沒有聽到您的語音，請再試一次。');
                } else {
                    this.addMessage('assistant', '語音識別出錯，請嘗試使用文字輸入。');
                }
            }
        });
    }
    
    /**
     * 初始化訂單核心
     */
    initOrderCore() {
        // 註冊訂單處理回調
        orderCore.registerCallbacks({
            onOrderProcessStart: () => {
                console.log('開始處理訂單...');
                this.setState('thinking');
            },
            onOrderProcessSuccess: (data) => {
                console.log('訂單處理成功:', data);
                this.addMessage('assistant', data.message);
            },
            onOrderProcessFail: (data) => {
                console.log('訂單處理失敗:', data);
                this.addMessage('assistant', data.message || '抱歉，我無法理解您的訂單，請再說一次。');
            },
            onOrderConfirm: (data) => {
                console.log('訂單確認結果:', data);
                if (data.success) {
                    this.addMessage('assistant', data.message);
                    
                    // 顯示訂單確認彈窗
                    setTimeout(() => {
                        if (window.Swal) {
                            Swal.fire({
                                title: '訂單已確認',
                                html: `
                                    <p>好的，尊貴的客人請稍候</p>
                                    <p>正在為您製作飲品</p>
                                    <p>您的取餐號碼是 <strong>${data.orderNumber}</strong></p>
                                    <p>預計等候時間：${data.waitingTime} 分鐘</p>
                                `,
                                icon: 'success',
                                timer: 5000,
                                timerProgressBar: true,
                                showConfirmButton: false
                            });
                        }
                    }, 1000);
                } else {
                    this.addMessage('assistant', data.message);
                }
            },
            onOrderCancel: () => {
                console.log('訂單已取消');
                // 不需要做任何事，訊息已經由 cancelOrder 函數返回
            },
            onOrderStatusUpdate: (data) => {
                console.log('訂單狀態更新:', data);
                this.addMessage('assistant', data.message);
            }
        });
    }
    
    /**
     * 初始化事件監聽器
     */
    initEventListeners() {
        // 發送按鈕點擊事件
        if (this.chatSendBtn) {
            this.chatSendBtn.addEventListener('click', () => {
                this.handleUserInput();
            });
        }
        
        // 輸入框回車事件
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleUserInput();
                }
            });
        }
        
        // 語音按鈕點擊事件
        if (this.voiceInputBtn) {
            this.voiceInputBtn.addEventListener('click', () => {
                voiceManager.toggleVoiceInput();
            });
        }
    }
    
    /**
     * 設置助手狀態
     * @param {string} state 狀態名稱 (idle, listening, speaking, thinking)
     */
    setState(state) {
        this.state = state;
        
        // 檢查是否有 Live2D 模型
        const waifuContainer = document.querySelector('#waifu');
        if (waifuContainer) {
            // 移除所有狀態類別
            waifuContainer.classList.remove('idle', 'listening', 'speaking', 'thinking');
            
            // 添加新狀態類別
            waifuContainer.classList.add(state);
            
            // Live2D 模型狀態控制
            if (state === 'speaking') {
                this.startMouthAnimation();
            } else {
                this.stopMouthAnimation();
            }
        } else {
            // 傳統圖片狀態控制
            const images = {
                idle: document.getElementById('assistantIdle'),
                speaking: document.getElementById('assistantSpeaking'),
                listening: document.getElementById('assistantListening'),
                thinking: document.getElementById('assistantThinking')
            };
            
            // 隱藏所有圖片
            Object.values(images).forEach(img => {
                if (img) img.classList.remove('active');
            });
            
            // 顯示對應狀態的圖片
            if (images[state]) {
                images[state].classList.add('active');
            } else if (images.idle) {
                images.idle.classList.add('active');
            }
        }
    }
    
    /**
     * 開始嘴巴動畫
     */
    startMouthAnimation() {
        // 停止現有動畫
        this.stopMouthAnimation();
        
        // 創建新動畫
        this.mouthAnimationInterval = setInterval(() => {
            const waifu = document.querySelector('#waifu');
            if (waifu) {
                waifu.classList.toggle('mouth-open');
            }
        }, 200);
    }
    
    /**
     * 停止嘴巴動畫
     */
    stopMouthAnimation() {
        if (this.mouthAnimationInterval) {
            clearInterval(this.mouthAnimationInterval);
            this.mouthAnimationInterval = null;
            
            const waifu = document.querySelector('#waifu');
            if (waifu) {
                waifu.classList.remove('mouth-open');
            }
        }
    }
    
    /**
     * 添加消息
     * @param {string} type 消息類型 (user, assistant)
     * @param {string} content 消息內容
     */
    addMessage(type, content) {
        if (!this.chatMessages) return;
        
        console.log(`添加${type}消息:`, content);
        
        // 創建消息元素
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        // 檢查是否是訂單確認消息
        const isOrderConfirmation = type === 'assistant' && 
                                  content.includes('確認一下訂單') && 
                                  content.includes('請問確認');
        
        if (isOrderConfirmation) {
            messageDiv.classList.add('order-confirmation');
        }
        
        // 添加消息內容
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        messageDiv.appendChild(contentDiv);
        
        // 如果是訂單確認消息，添加確認和取消按鈕
        if (isOrderConfirmation) {
            const buttonsDiv = document.createElement('div');
            buttonsDiv.className = 'confirm-buttons';
            
            // 確認按鈕
            const confirmBtn = document.createElement('button');
            confirmBtn.className = 'confirm-btn';
            confirmBtn.textContent = '確認訂單';
            confirmBtn.addEventListener('click', () => this.handleOrderConfirmation(true));
            
            // 取消按鈕
            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'cancel-btn';
            cancelBtn.textContent = '取消訂單';
            cancelBtn.addEventListener('click', () => this.handleOrderConfirmation(false));
            
            buttonsDiv.appendChild(confirmBtn);
            buttonsDiv.appendChild(cancelBtn);
            messageDiv.appendChild(buttonsDiv);
        }
        
        // 將消息添加到聊天容器
        this.chatMessages.appendChild(messageDiv);
        
        // 滾動到底部
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // 如果是助手消息，播放語音
        if (type === 'assistant') {
            voiceManager.speak(content);
        }
    }
    
    /**
     * 處理用戶輸入
     */
    async handleUserInput() {
        // 獲取用戶輸入並清空輸入框
        const input = this.chatInput?.value.trim();
        if (!input) return;
        
        this.chatInput.value = '';
        
        // 添加用戶消息
        this.addMessage('user', input);
        
        // 設置思考狀態
        this.setState('thinking');
        
        // 檢查訂單狀態
        const orderState = orderCore.getOrderState();
        
        // 如果有待確認的訂單，處理訂單確認
        if (orderState.hasActiveOrder && !orderState.isConfirmed && orderState.state === 'confirming') {
            await this.handleOrderConfirmText(input);
            return;
        }
        
        // 檢查是否為點餐意圖
        if (orderCore.isOrderIntent(input)) {
            console.log('檢測到點餐意圖，開始處理訂單...');
            await this.processOrder(input);
        } else {
            // 一般聊天處理
            await this.processChatResponse(input);
        }
    }
    
    /**
     * 處理文本形式的訂單確認
     * @param {string} input 用戶輸入
     */
    async handleOrderConfirmText(input) {
        const confirmKeywords = ['確認', '好', '是', '沒問題', '可以', '對', '要', '正確', '是的', '好的', '確定', '嗯', '恩', '行'];
        const cancelKeywords = ['取消', '不要', '不', '算了', '錯', '重新', '不行', '不對', '不是'];
        
        const isConfirm = confirmKeywords.some(keyword => input.includes(keyword)) || 
                         /^[嗯恩]$/.test(input) || 
                         /^好$/.test(input) || 
                         /^是$/.test(input) ||
                         /^確認$/.test(input);
                         
        const isCancel = cancelKeywords.some(keyword => input.includes(keyword));
        
        if (isConfirm && !isCancel) {
            // 確認訂單
            console.log('用戶確認訂單');
            await orderCore.confirmOrder();
        } else if (isCancel) {
            // 取消訂單
            console.log('用戶取消訂單');
            const message = orderCore.cancelOrder();
            this.addMessage('assistant', message);
        } else {
            // 不明確的回覆
            console.log('訂單確認回覆不明確');
            this.addMessage('assistant', '請明確告訴我是「確認」還是「取消」訂單。');
        }
    }
    
    /**
     * 處理訂單確認按鈕點擊
     * @param {boolean} isConfirm 是否確認
     */
    async handleOrderConfirmation(isConfirm) {
        if (isConfirm) {
            // 確認訂單
            this.setState('thinking');
            this.addMessage('user', '確認訂單');
            await orderCore.confirmOrder();
        } else {
            // 取消訂單
            this.addMessage('user', '取消訂單');
            const message = orderCore.cancelOrder();
            this.addMessage('assistant', message);
        }
    }
    
    /**
     * 處理訂單
     * @param {string} text 用戶輸入
     */
    async processOrder(text) {
        // 先顯示處理中消息
        this.addMessage('assistant', '正在為您處理訂單，請稍候...');
        
        // 分析訂單
        await orderCore.analyzeOrder(text);
        
        // 所有訂單處理結果已通過回調處理
    }
    
    /**
     * 處理聊天回應
     * @param {string} text 用戶輸入
     */
    async processChatResponse(text) {
        try {
            // 設置思考狀態
            this.setState('thinking');
            
            // 發送到後端分析
            const response = await fetch('/analyze_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            
            const result = await response.json();
            
            // 檢查是否有回應
            if (result && result.reply) {
                // 顯示回應
                this.addMessage('assistant', result.reply);
            } else {
                // 使用預設回應
                this.addMessage('assistant', '抱歉，我不太理解您的意思。請問您想點什麼飲料呢？');
            }
        } catch (error) {
            console.error('處理聊天回應時出錯:', error);
            this.addMessage('assistant', '抱歉，系統暫時遇到問題，請稍後再試。');
        }
    }
}

// 導出助手核心
export default AssistantCore;
