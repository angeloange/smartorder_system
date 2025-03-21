// 全局變量，防止重複初始化
window.assistantInitialized = false;
window.virtualAssistant = null;

class VirtualAssistant {
    constructor() {
        console.log('VirtualAssistant 初始化中...');
        
        // 單例模式：防止重複創建實例
        if (window.assistantInitialized) {
            console.log('虛擬助手已初始化，跳過重複創建');
            return window.virtualAssistant;
        }
        
        // 標記為已初始化
        window.assistantInitialized = true;
        window.virtualAssistant = this;
        
        // 基本UI元素
        this.messages = [];
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.chatSendBtn = document.getElementById('chatSendBtn');
        this.voiceInputBtn = document.getElementById('chatVoiceBtn');
        
        // 表情狀態定義
        this.EMOTIONS = {
            IDLE: 'idle',           // 閒置
            GREETING: 'happy',      // 問候
            THINKING: 'thinking',   // 思考
            HAPPY: 'happy',         // 開心
            CONFUSED: 'confused',   // 困惑
            EXCITED: 'excited'      // 興奮
        };
        
        // 訂單狀態
        this.currentOrder = null;
        this.orderConfirmed = false;
        this.currentOrderNumber = null;
        this.currentEmotion = this.EMOTIONS.IDLE;
        
        // 語音相關
        this.synth = window.speechSynthesis;
        this.voice = null;
        this.isSpeaking = false;
        this.initVoice();
        
        // 語音識別
        this.recognition = null;
        this.isListening = false;
        this.initSpeechRecognition();
        
        // 初始化
        this.initEventListeners();
        this.initSocketConnection();
        
        // 歡迎訊息（僅一次）
        setTimeout(() => {
            this.setEmotion(this.EMOTIONS.GREETING);
            this.addMessage('assistant', '您好！我是您的智慧點餐助手。請問您今天想喝什麼呢？或是需要我為您推薦飲品？');
        }, 1000);
    }
    
    // ===== 語音合成與處理 =====
    
    initVoice() {
        if (this.synth) {
            // 等待語音列表載入
            const checkVoices = () => {
                const voices = this.synth.getVoices();
                if (voices.length > 0) {
                    // 優先順序選擇更自然的語音
                    const preferredVoices = [
                        'Microsoft Hanhan - Chinese (Traditional, Taiwan)',  // 最自然的微軟台灣語音
                        'Microsoft Zhiwei - Chinese (Simplified, PRC)',      // 較自然的微軟語音
                        'Microsoft HsiaoChen - Chinese (Traditional, Taiwan)',
                        'Google 中文（臺灣）',
                        'Mei-Jia'
                    ];
                    
                    // 按優先順序選擇語音
                    for (const voiceName of preferredVoices) {
                        const foundVoice = voices.find(v => v.name === voiceName);
                        if (foundVoice) {
                            this.voice = foundVoice;
                            console.log('已選用優質語音:', this.voice.name);
                            return;
                        }
                    }
                    
                    // 選擇任何中文語音
                    this.voice = voices.find(v => 
                        v.lang === 'zh-TW' || 
                        v.lang === 'zh-HK' || 
                        v.lang === 'zh-CN' ||
                        v.lang.includes('cmn') || 
                        v.lang.includes('yue') ||
                        v.lang.includes('zh')
                    );
                    
                    console.log('已設定語音:', this.voice ? this.voice.name : '使用預設語音');
                } else {
                    setTimeout(checkVoices, 100);
                }
            };
            
            if (this.synth.onvoiceschanged !== undefined) {
                this.synth.onvoiceschanged = checkVoices;
            }
            checkVoices();
        } else {
            console.warn('瀏覽器不支援語音合成');
        }
    }
    
    speak(text) {
        if (!text || text.trim() === '') return;
        
        // 確保消息顯示在界面上
        if (!document.querySelector('.message.assistant:last-child .message-content')?.textContent?.includes(text)) {
            // 這裡使用普通的DOM操作添加消息，而不是調用addMessage避免遞歸
            const messageDiv = document.createElement('div');
            messageDiv.className = `message assistant`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = text;
            
            messageDiv.appendChild(contentDiv);
            this.chatMessages.appendChild(messageDiv);
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
        
        // 設置虛擬助手為說話狀態
        this.setAssistantState('speaking');
        this.isSpeaking = true;
        
        // 使用 Azure 語音 API 生成語音
        fetch('/api/get_speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                text: text,
                style: 'female_warm',
                rate: 1.2  // 語速調整
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 創建音頻元素並播放
                const audio = new Audio(data.audio_url);
                
                // 保存文件名
                const audioFilename = data.filename;
                
                // 音頻結束時設置空閒狀態
                audio.onended = () => {
                    this.isSpeaking = false;
                    this.setAssistantState('idle');
                    
                    // 刪除已播放完的文件
                    if (audioFilename) {
                        fetch('/api/delete_audio', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ filename: audioFilename })
                        }).catch(e => console.warn('刪除語音文件失敗:', e));
                    }
                };
                
                // 音頻錯誤處理
                audio.onerror = (err) => {
                    console.error('音頻播放錯誤:', err);
                    this.isSpeaking = false;
                    this.setAssistantState('idle');
                };
                
                // 播放音頻 - 無需用戶交互
                const playPromise = audio.play();
                
                if (playPromise !== undefined) {
                    playPromise.catch(err => {
                        console.warn('自動播放受限，嘗試靜音播放:', err);
                        
                        // 嘗試靜音自動播放
                        audio.muted = true;
                        audio.play().then(() => {
                            // 短暫播放後取消靜音
                            setTimeout(() => {
                                audio.muted = false;
                            }, 100);
                        }).catch(err2 => {
                            console.error('靜音播放也失敗:', err2);
                            this.isSpeaking = false;
                            this.setAssistantState('idle');
                        });
                    });
                }
            } else {
                console.error('語音生成失敗:', data.error);
                this.isSpeaking = false;
                this.setAssistantState('idle');
            }
        })
        .catch(err => {
            console.error('無法連接到語音API:', err);
            this.isSpeaking = false;
            this.setAssistantState('idle');
        });
    }
    
    // ===== 語音識別功能 =====
    
    initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.lang = 'zh-TW';
            this.recognition.interimResults = false;
            this.recognition.maxAlternatives = 1;
            
            this.recognition.onresult = (event) => {
                const speechResult = event.results[0][0].transcript;
                console.log('語音識別結果:', speechResult);
                this.chatInput.value = speechResult;
                this.handleUserInput();
            };
            
            this.recognition.onerror = (event) => {
                console.error('語音識別錯誤:', event.error);
                this.stopVoiceInput();
                
                if (event.error === 'no-speech') {
                    this.addMessage('assistant', '我沒有聽到您的語音，請再試一次。');
                } else {
                    this.addMessage('assistant', '語音識別出錯，請嘗試使用文字輸入。');
                }
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
                if (this.voiceInputBtn) {
                    this.voiceInputBtn.classList.remove('recording');
                }
            };
        } else {
            console.warn('瀏覽器不支援語音識別');
            if (this.voiceInputBtn) {
                this.voiceInputBtn.style.display = 'none';
            }
        }
    }
    
    toggleVoiceInput() {
        if (!this.recognition) return;
        
        if (this.isListening) {
            this.stopVoiceInput();
        } else {
            this.startVoiceInput();
        }
    }
    
    startVoiceInput() {
        if (this.recognition) {
            try {
                this.recognition.start();
                this.isListening = true;
                if (this.voiceInputBtn) {
                    this.voiceInputBtn.classList.add('recording');
                }
                this.setEmotion(this.EMOTIONS.THINKING);
                this.addMessage('assistant', '我在聆聽，請說出您的需求...');
            } catch (error) {
                console.error('無法啟動語音識別:', error);
            }
        }
    }
    
    stopVoiceInput() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
            if (this.voiceInputBtn) {
                this.voiceInputBtn.classList.remove('recording');
            }
        }
    }
    
    // ===== 界面與情感控制 =====
    
    setAssistantState(state) {
        // 只在狀態真正變化時才執行切換
        const currentState = state === 'speaking' ? 'speaking' : 'idle';
        
        try {
            // 控制 Live2D 模型狀態
            const waifuElement = document.querySelector('#waifu');
            if (waifuElement) {
                if (currentState === 'speaking') {
                    waifuElement.setAttribute('data-speaking', 'true');
                    
                    // 顯示說話動畫
                    this.mouthAnimation = setInterval(() => {
                        waifuElement.classList.toggle('mouth-open');
                    }, 150); // 嘴巴開合頻率
                    
                    // 顯示提示框
                    const waifuTips = document.getElementById('waifu-tips');
                    if (waifuTips) {
                        waifuTips.innerHTML = '我在為您服務！';
                        waifuTips.style.opacity = 1;
                        setTimeout(() => {
                            waifuTips.style.opacity = 0;
                        }, 3000);
                    }
                    
                    // 觸發說話動作
                    if (typeof window.showLive2DMotion === 'function') {
                        window.showLive2DMotion('tap');
                    }
                } else {
                    waifuElement.setAttribute('data-speaking', 'false');
                    
                    // 停止嘴巴動畫
                    if (this.mouthAnimation) {
                        clearInterval(this.mouthAnimation);
                        waifuElement.classList.remove('mouth-open');
                    }
                    
                    // 觸發閒置動作
                    if (typeof window.showLive2DMotion === 'function') {
                        window.showLive2DMotion('idle');
                    }
                }
            }
        } catch (e) {
            console.error('Live2D 控制錯誤:', e);
        }
    }
    
    setEmotion(emotion) {
        if (this.currentEmotion === emotion) return;
        
        this.currentEmotion = emotion;
        console.log('設置表情:', emotion);
        
        // 控制 Live2D 模型
        try {
            const waifuElement = document.querySelector('#waifu');
            if (waifuElement) {
                // 移除所有表情類
                waifuElement.classList.remove(
                    'emotion-idle', 
                    'emotion-happy', 
                    'emotion-thinking', 
                    'emotion-confused', 
                    'emotion-excited'
                );
                
                // 添加新表情類
                waifuElement.classList.add(`emotion-${emotion}`);
                
                // 如果有特定表情的 Live2D 動作，調用它
                if (typeof window.showLive2DExpression === 'function') {
                    window.showLive2DExpression(emotion);
                } else if (typeof window.showLive2DMotion === 'function') {
                    // 動作映射
                    const motionMap = {
                        'idle': 'idle',
                        'happy': 'tap',
                        'thinking': 'flick_head',
                        'confused': 'shake',
                        'excited': 'tap_body'
                    };
                    window.showLive2DMotion(motionMap[emotion] || 'tap');
                }
            }
        } catch (e) {
            console.error('設置表情出錯:', e);
        }
    }
    
    setEmotionBasedOnText(text) {
        if (text.includes('很高興') || text.includes('太好了') || 
            text.includes('謝謝') || text.includes('歡迎')) {
            this.setEmotion(this.EMOTIONS.HAPPY);
        } else if (text.includes('讓我想想') || text.includes('您是指') || 
                  text.includes('請問') || text.includes('?') || 
                  text.includes('？')) {
            this.setEmotion(this.EMOTIONS.THINKING);
        } else if (text.includes('抱歉') || text.includes('不好意思') || 
                  text.includes('我不確定')) {
            this.setEmotion(this.EMOTIONS.CONFUSED);
        } else if (text.includes('!') || text.includes('！') || 
                  text.includes('推薦') || text.includes('最受歡迎')) {
            this.setEmotion(this.EMOTIONS.EXCITED);
        } else {
            // 默認表情
            this.setEmotion(this.EMOTIONS.IDLE);
        }
    }
    
    // ===== 消息處理 =====
    
    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // 只有助手消息需要播放語音，但不在這裡調用speak以避免重複
        // 注意：user 消息不需要調用 speak
        if (type === 'assistant' && !this.isSpeaking) {
            this.speak(content);
        }
    }
    
    processResponse(text) {
        if (!text || text.trim() === '') return;
        
        // 直接使用speak方法，它會處理消息顯示和語音
        if (!this.isSpeaking) {
            this.speak(text);
        }
    }
    
    // ===== 用戶輸入處理 =====
    
    initEventListeners() {
        // 發送按鈕點擊事件
        if (this.chatSendBtn) {
            this.chatSendBtn.addEventListener('click', () => {
                this.handleUserInput();
            });
        }
        
        // 輸入框按 Enter 事件
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
                this.toggleVoiceInput();
            });
        }
    }
    
    async handleUserInput() {
        const input = this.chatInput.value.trim();
        if (!input) return;
        
        // 清空輸入框
        this.chatInput.value = '';
        
        // 顯示用戶消息
        this.addMessage('user', input);
        
        // 設置思考表情
        this.setEmotion(this.EMOTIONS.THINKING);
        
        // 檢查是否包含明確的點餐關鍵詞
        const orderKeywords = ['奶茶', '珍珠', '茶', '咖啡', '拿鐵', '美式', '綠茶', '紅茶', '點一杯', '要一杯'];
        const isDirectOrder = orderKeywords.some(keyword => input.includes(keyword));
        
        // 優先處理訂單確認
        if (this.currentOrder && !this.orderConfirmed && 
            (input.includes('確認') || input.includes('取消') || 
             input.includes('好的') || input.includes('不要'))) {
            // 處理訂單確認回覆
            this.handleOrderConfirmation(input);
            return;
        }
        
        // 如果是明確的飲料訂單，直接分析訂單
        if (isDirectOrder) {
            console.log('檢測到直接點餐，使用訂單分析器');
            await this.processOrder(input);
            return;
        }
        
        try {
            // 使用聊天分析API
            const response = await fetch('/analyze_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: input })
            });
            
            const result = await response.json();
            console.log('聊天分析結果:', result);
            
            if (result.status === 'success') {
                // 處理返回的意圖
                if (result.order_details && result.order_details.length > 0) {
                    // 如果有解析出訂單詳情，表示是點餐意圖
                    this.currentOrder = result.order_details;
                    this.orderConfirmed = false;
                    
                    const orderText = result.order_details.map(item => 
                        `${item.size || ''}${item.ice || ''}${item.sugar || ''}${item.drink_name}`
                    ).join('、');
                    
                    this.setEmotion(this.EMOTIONS.HAPPY);
                    this.processResponse(`我幫您確認一下訂單：${orderText}\n請問確認訂購嗎？`);
                } else {
                    // 一般對話回覆
                    this.setEmotionBasedOnText(result.reply);
                    this.processResponse(result.reply);
                    
                    // 如果意圖是點餐但沒有解析出具體訂單，提示用戶
                    if (result.intent === 'order' && !result.order_details) {
                        setTimeout(() => {
                            this.setEmotion(this.EMOTIONS.THINKING);
                            this.processResponse("您想點什麼飲料呢？我們有多種茶飲和咖啡。");
                        }, 2000);
                    }
                }
            } else {
                // 錯誤處理
                this.setEmotion(this.EMOTIONS.CONFUSED);
                this.processResponse("抱歉，我好像沒聽懂。您能換個方式說明嗎？");
            }
        } catch (error) {
            console.error('處理用戶輸入時出錯:', error);
            this.setEmotion(this.EMOTIONS.CONFUSED);
            this.processResponse("抱歉，系統遇到了問題，請稍後再試。");
        }
    }
    
    // ===== 訂單處理 =====
    
    handleOrderConfirmation(input) {
        if (input.includes('確認') || input.includes('好') || 
            input.includes('沒問題') || input.includes('是') || 
            input.includes('對') || input.includes('可以')) {
            this.setEmotion(this.EMOTIONS.EXCITED);
            this.confirmOrder();
        } else if (input.includes('取消') || input.includes('不') || 
                  input.includes('算了') || input.includes('換') || 
                  input.includes('重新')) {
            this.setEmotion(this.EMOTIONS.CONFUSED);
            this.cancelOrder();
        } else {
            this.setEmotion(this.EMOTIONS.THINKING);
            this.processResponse("請問要確認這個訂單嗎？可以回答「確認」或「取消」。");
        }
    }
    
    async processOrder(input) {
        console.log('開始處理訂單輸入:', input);
        this.setEmotion(this.EMOTIONS.THINKING);
        
        try {
            // 先顯示處理中消息
            this.addMessage('assistant', '正在為您處理訂單，請稍候...');
            
            const response = await fetch('/analyze_text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: input })
            });

            const result = await response.json();
            console.log('訂單分析結果:', result);
            
            if (result.status === 'success' && result.order_details && result.order_details.length > 0) {
                this.currentOrder = result.order_details;
                this.orderConfirmed = false;
                
                // 格式化訂單信息
                const orderText = result.order_details.map(item => 
                    `${item.size || '中杯'}${item.ice || '正常冰'}${item.sugar || '全糖'}${item.drink_name}`
                ).join('、');
                
                this.setEmotion(this.EMOTIONS.HAPPY);
                this.processResponse(`我幫您確認一下訂單：${orderText}\n請問確認訂購嗎？`);
            } else {
                this.setEmotion(this.EMOTIONS.CONFUSED);
                this.processResponse('抱歉，我沒能理解您的點餐需求。請您嘗試說明想要的飲料名稱。');
            }
        } catch (error) {
            console.error('處理訂單時發生錯誤:', error);
            this.setEmotion(this.EMOTIONS.CONFUSED);
            this.processResponse('抱歉，系統處理訂單時發生錯誤，請稍後再試。');
        }
    }

    async confirmOrder() {
        this.setEmotion(this.EMOTIONS.EXCITED);
        
        try {
            console.log('正在確認訂單:', this.currentOrder);
            
            // 先給用戶反饋
            this.addMessage('assistant', '正在確認您的訂單，請稍候...');
            
            const response = await fetch('/confirm_order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_details: this.currentOrder })
            });

            const result = await response.json();
            console.log('訂單確認結果:', result);
            
            if (result.status === 'success') {
                this.orderConfirmed = true;
                this.currentOrderNumber = result.order_number;
                
                // 先顯示訂單確認消息
                this.addMessage('assistant', `訂單已確認！您的取餐號碼是 ${result.order_number}，謝謝您的光臨。`);
                
                // 然後顯示 SweetAlert
                setTimeout(() => {
                    Swal.fire({
                        title: '訂單已確認',
                        html: `
                            <p>好的，尊貴的客人請稍候</p>
                            <p>正在為您製作飲品</p>
                            <p>您的取餐號碼是 <strong>${result.order_number}</strong></p>
                        `,
                        icon: 'success',
                        timer: 5000,
                        timerProgressBar: true,
                        showConfirmButton: false
                    }).then(() => {
                        // 5秒後重置頁面
                        location.reload();
                    });
                }, 3000);
            } else {
                this.setEmotion(this.EMOTIONS.CONFUSED);
                throw new Error(result.message || '訂單確認失敗');
            }
        } catch (error) {
            console.error('確認訂單時出錯:', error);
            this.setEmotion(this.EMOTIONS.CONFUSED);
            this.addMessage('assistant', '抱歉，訂單確認失敗，請稍後再試。');
        }
    }

    cancelOrder() {
        this.currentOrder = null;
        this.orderConfirmed = false;
        this.setEmotion(this.EMOTIONS.THINKING);
        this.addMessage('assistant', '好的，已取消訂單。請問您想重新點餐嗎？');
    }

    // ===== WebSocket 連接 =====
    
    initSocketConnection() {
        try {
            // 自動檢測正確的連接地址
            const socketUrl = window.location.origin;
            console.log('嘗試連接 Socket.IO:', socketUrl);
            
            this.socket = io(socketUrl, {
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
            });
            
            this.socket.on('connect', () => {
                console.log('Socket.IO 已連接');
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Socket.IO 連接錯誤:', error);
            });
            
            this.socket.on('order_status_update', (data) => {
                console.log('收到訂單狀態更新:', data);
                this.handleOrderStatusUpdate(data);
            });
        } catch (error) {
            console.error('初始化 Socket.IO 時發生錯誤:', error);
        }
    }

    handleOrderStatusUpdate(data) {
        if (data.order_number && data.status && 
            this.currentOrderNumber === data.order_number) {
            const statusMessage = `您的訂單 ${data.order_number} 狀態已更新為: ${data.status}`;
            this.addMessage('assistant', statusMessage);
        }
    }
}

// ===== 初始化代碼 =====

// 檢測移動裝置
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// 單一初始化入口 - 防止重複初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 載入完成，準備初始化虛擬助手...');
    
    // 檢查是否已經初始化
    if (window.virtualAssistant) {
        console.log('虛擬助手已初始化，跳過');
        return;
    }
    
    // 移動設備顯示解鎖按鈕，桌面直接初始化
    if (isMobileDevice()) {
        createMobileUnlockButton();
    } else {
        initializeAssistant();
    }
});

// 為移動設備創建解鎖按鈕
function createMobileUnlockButton() {
    const unlockDiv = document.createElement('div');
    unlockDiv.className = 'audio-unlock-container';
    unlockDiv.innerHTML = `
        <button class="unlock-button">
            <i class="fas fa-volume-up"></i> 點擊啟用語音
        </button>
    `;
    document.body.appendChild(unlockDiv);
    
    // 添加樣式
    const style = document.createElement('style');
    style.textContent = `
        .audio-unlock-container {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.8);
            padding: 20px;
            border-radius: 10px;
            z-index: 10000;
            text-align: center;
        }
        .unlock-button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
    `;
    document.head.appendChild(style);
    
    // 點擊解鎖按鈕
    const unlockButton = unlockDiv.querySelector('.unlock-button');
    unlockButton.addEventListener('click', () => {
        // 播放一個靜音音頻來解鎖
        const silentAudio = new Audio("data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjMyLjEwNAAAAAAAAAAAAAAA//tQwAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAABAAADQgD///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////8AAAA5TEFNRTMuMTAwBK8AAAAAAAAAABUgJAUHQQAB9gAAA0LGZPx9AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//tQxAADwAABpAAAACAAADSAAAAETEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV");
        silentAudio.play().catch(err => console.error('音頻解鎖失敗:', err));
        
        // 啟動語音合成解鎖
        const synth = window.speechSynthesis;
        if (synth) {
            const utterance = new SpeechSynthesisUtterance('');
            utterance.volume = 0.01;
            synth.speak(utterance);
        }
        
        // 隱藏解鎖按鈕
        unlockDiv.style.display = 'none';
        
        // 初始化虛擬助手
        initializeAssistant();
    });
}

// 初始化助手實例
function initializeAssistant() {
    if (!window.virtualAssistant) {
        try {
            // 隱藏可能存在的解鎖容器
            const unlockContainer = document.getElementById('audioUnlockContainer');
            if (unlockContainer) {
                unlockContainer.style.display = 'none';
            }
            
            // 嘗試自動解鎖音頻
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const buffer = audioContext.createBuffer(1, 1, 22050);
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(0);
            
            // 創建虛擬助手實例
            window.virtualAssistant = new VirtualAssistant();
            console.log('虛擬助手已成功初始化');
        } catch (error) {
            console.error('初始化虛擬助手時出錯:', error);
            // 即使出錯也嘗試創建實例
            window.virtualAssistant = new VirtualAssistant();
        }
    }
}