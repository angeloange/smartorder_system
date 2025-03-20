class VirtualAssistant {
    constructor() {
        console.log('VirtualAssistant 初始化中...');
        
        // 檢查是否已經初始化過，防止重複初始化
        if (window.assistantInitialized) {
            console.log('虛擬助手已初始化，跳過');
            return;
        }
        window.assistantInitialized = true;
        
        this.messages = [];
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.chatSendBtn = document.getElementById('chatSendBtn');
        this.voiceInputBtn = document.getElementById('chatVoiceBtn');
        
        // 訂單狀態
        this.currentOrder = null;
        this.orderConfirmed = false;
        
        // 語音合成
        this.synth = window.speechSynthesis;
        this.voice = null;
        this.isSpeaking = false;
        this.initVoice();
        
        // 語音識別
        this.recognition = null;
        this.isListening = false;
        this.initSpeechRecognition();
        
        // 初始化事件綁定
        this.initEventListeners();
        
        // 添加 Socket.IO 連接
        this.initSocketConnection();
        
        // 展示歡迎訊息
        setTimeout(() => {
            this.addMessage('assistant', '您好！我是您的智慧點餐助手。請問您今天想喝什麼呢？');
        }, 1000);
    }
    
    // 初始化語音合成 - 選擇最優質的中文語音
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
                    
                    // 嘗試按優先順序選擇語音
                    for (const voiceName of preferredVoices) {
                        const foundVoice = voices.find(v => v.name === voiceName);
                        if (foundVoice) {
                            this.voice = foundVoice;
                            console.log('已選用優質語音:', this.voice.name);
                            return;
                        }
                    }
                    
                    // 如果沒找到優先語音，選擇任何中文語音
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
    
    // 說話功能 - 增強錯誤處理和回退機制
    speak(text) {
        if (!this.synth) {
            console.warn('語音合成不可用');
            this.setAssistantState('speaking');
            setTimeout(() => this.setAssistantState('idle'), text.length * 80);
            return;
        }
        
        try {
            // 取消所有正在播放的語音
            this.synth.cancel();
            
            // 預處理文本
            const processedText = this.addNaturalPauses(text);
            
            const utterance = new SpeechSynthesisUtterance(processedText);
            
            // 根據語音類型調整參數
            if (this.voice && this.voice.name.includes('Microsoft')) {
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
            } else {
                utterance.rate = 1.1;
                utterance.pitch = 1.05;
            }
            
            utterance.volume = 1.0;
            
            // 設定語音
            if (this.voice) {
                utterance.voice = this.voice;
                console.log('使用語音:', this.voice.name);
            } else {
                console.warn('未找到合適語音，使用默認');
            }
            
            // 說話開始
            this.isSpeaking = true;
            this.setAssistantState('speaking');
            
            // 添加調試信息
            console.log('嘗試播放語音:', processedText);
            
            // 設置超時回退，防止語音無法播放但未觸發onend
            const speakTimeout = setTimeout(() => {
                if (this.isSpeaking) {
                    console.warn('語音播放超時，強制結束');
                    this.isSpeaking = false;
                    this.setAssistantState('idle');
                }
            }, Math.min(text.length * 120, 10000));
            
            // 說話結束時的回調
            utterance.onend = () => {
                clearTimeout(speakTimeout);
                this.isSpeaking = false;
                this.setAssistantState('idle');
                console.log('語音播放完成');
            };
            
            // 發生錯誤時
            utterance.onerror = (err) => {
                clearTimeout(speakTimeout);
                console.error('語音合成錯誤:', err);
                this.isSpeaking = false;
                this.setAssistantState('idle');
            };
            
            // 開始播放
            this.synth.speak(utterance);
            
        } catch (error) {
            console.error('語音合成出現異常:', error);
            this.isSpeaking = false;
            this.setAssistantState('idle');
        }
    }
    // 新增：添加自然停頓的輔助方法
    addNaturalPauses(text) {
        // 在標點符號後添加短暫停頓
        let processedText = text.replace(/([，。！？：；])/g, '$1,');
        
        // 處理特定句型來增加自然度
        processedText = processedText
            .replace(/請問您今天想喝什麼呢？/g, '請問您，今天想喝什麼呢？')
            .replace(/我幫您確認一下訂單：/g, '我幫您，確認一下，訂單：')
            .replace(/請問確認訂購嗎？/g, '請問，確認訂購嗎？')
            .replace(/訂單已確認！/g, '訂單已確認！')
            .replace(/謝謝您的光臨。/g, '謝謝您的，光臨。');
        
        return processedText;
    }
    
    // 初始化語音識別
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
    
    // 切換語音輸入狀態
    toggleVoiceInput() {
        if (!this.recognition) return;
        
        if (this.isListening) {
            this.stopVoiceInput();
        } else {
            this.startVoiceInput();
        }
    }
    
    // 開始語音輸入
    startVoiceInput() {
        if (this.recognition) {
            try {
                this.recognition.start();
                this.isListening = true;
                if (this.voiceInputBtn) {
                    this.voiceInputBtn.classList.add('recording');
                }
                this.setAssistantState('stfu'); // 助手切換到聆聽狀態
            } catch (error) {
                console.error('無法啟動語音識別:', error);
            }
        }
    }
    
    // 停止語音輸入
    stopVoiceInput() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
            if (this.voiceInputBtn) {
                this.voiceInputBtn.classList.remove('recording');
            }
        }
    }
    
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
    
    // 設置虛擬助手狀態
// 找到 setAssistantState 方法並修改
setAssistantState(state) {
    // 只在狀態真正變化時才執行切換
    const currentState = state === 'speaking' ? 'speaking' : 'idle';
    
    try {
        // 控制 Live2D 模型狀態
        const waifuElement = document.querySelector('#waifu');
        if (waifuElement) {
            if (currentState === 'speaking') {
                waifuElement.setAttribute('data-speaking', 'true');
                
                // 顯示提示框
                const waifuTips = document.getElementById('waifu-tips');
                if (waifuTips) {
                    waifuTips.innerHTML = '我在聽著呢！';
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
                
                // 觸發閒置動作
                if (typeof window.showLive2DMotion === 'function') {
                    window.showLive2DMotion('idle');
                }
            }
        }
    } catch (e) {
        console.error('Live2D 控制錯誤:', e);
        
        // 如果發生錯誤，可以考慮回退到原始的圖片方案
        // 取消註釋下方代碼即可啟用原始方案
        /*
        const currentActiveId = document.querySelector('.assistant-image.active')?.id;
        const targetId = currentState === 'speaking' ? 'assistantSpeaking' : 'assistantIdle';
        
        // 如果狀態沒變，就不需要切換
        if (currentActiveId === targetId) return;
        
        // 隱藏所有狀態
        document.querySelectorAll('.assistant-image').forEach(img => {
            img.classList.remove('active');
        });
        
        // 設置新狀態
        document.getElementById(targetId).classList.add('active');
        */
    }
}


    // 添加消息的方法 - 移除之前的延遲計算，使用語音事件控制
    async addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        // 如果是助手消息，播放語音
        if (type === 'assistant') {
            // 直接調用speak，狀態切換由speak方法內的事件處理
            this.speak(content);
        }
    }
    
    // 處理用戶輸入
    async handleUserInput() {
        const input = this.chatInput.value.trim();
        if (!input) return;
        
        // 清空輸入框並顯示用戶消息
        this.chatInput.value = '';
        this.addMessage('user', input);
        
        // 設置思考狀態
        this.setAssistantState('basic');
        
        try {
            if (this.currentOrder && !this.orderConfirmed) {
                // 處理訂單確認
                if (input.includes('確認') || input.includes('好') || input.includes('沒問題')) {
                    await this.confirmOrder();
                } else if (input.includes('取消') || input.includes('不') || input.includes('算了')) {
                    this.cancelOrder();
                } else {
                    this.addMessage('assistant', '請告訴我要確認還是取消訂單？');
                }
            } else {
                // 處理新訂單
                await this.processOrder(input);
            }
        } catch (error) {
            console.error('處理用戶輸入時出錯:', error);
            this.addMessage('assistant', '抱歉，處理您的請求時發生錯誤，請稍後再試。');
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
                this.orderConfirmed = true;
                this.currentOrder = null;
                
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

    // 初始化 Socket.IO 連接
    initSocketConnection() {
        try {
            // 自動檢測正確的連接地址
            const socketUrl = window.location.origin;
            console.log('嘗試連接 Socket.IO:', socketUrl);
            
            this.socket = io(socketUrl, {
                transports: ['websocket', 'polling'], // 強制嘗試 WebSocket，失敗後回退到長輪詢
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
                // 處理訂單狀態更新
                this.handleOrderStatusUpdate(data);
            });
        } catch (error) {
            console.error('初始化 Socket.IO 時發生錯誤:', error);
        }
    }

    // 處理訂單狀態更新
    handleOrderStatusUpdate(data) {
        // 如果收到訂單狀態更新，可以更新 UI 顯示
        if (data.order_number && data.status) {
            if (this.currentOrderNumber === data.order_number) {
                // 更新訂單狀態顯示
                const statusMessage = `您的訂單 ${data.order_number} 狀態已更新為: ${data.status}`;
                this.addMessage('assistant', statusMessage);
            }
        }
    }
}

// 當 DOM 加載完成後初始化一次
// 當 DOM 加載完成後設置解鎖按鈕
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 載入完成，設置音頻解鎖按鈕...');
    
    // 創建解鎖容器
    const unlockContainer = document.createElement('div');
    unlockContainer.className = 'audio-unlock-container';
    unlockContainer.id = 'audioUnlockContainer';
    unlockContainer.innerHTML = `
        <div class="unlock-content">
            <h3>開始使用智慧點餐</h3>
            <p>點擊下方按鈕啟動語音功能</p>
            <button id="unlockAudioBtn" class="unlock-button">
                <i class="fas fa-volume-up"></i> 啟動語音系統
            </button>
            <div class="device-note">（此步驟在移動設備上必需）</div>
        </div>
    `;
    
    // 添加到頁面頂部
    document.body.insertBefore(unlockContainer, document.body.firstChild);
    
    // 添加樣式
    const style = document.createElement('style');
    style.textContent = `
        .audio-unlock-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .unlock-content {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            max-width: 80%;
        }
        .unlock-button {
            background-color: #4caf50;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 18px;
            border-radius: 30px;
            margin: 20px 0;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }
        .unlock-button:hover {
            background-color: #45a049;
        }
        .device-note {
            font-size: 12px;
            color: #777;
            margin-top: 15px;
        }
    `;
    document.head.appendChild(style);
    
    // 添加點擊事件
    document.getElementById('unlockAudioBtn').addEventListener('click', async () => {
        try {
            console.log('嘗試解鎖音頻...');
            
            // 使用現代音頻 API 解鎖 
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // 創建並播放靜音數據來解鎖
            const buffer = audioContext.createBuffer(1, 1, 22050);
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(0);
            
            // 嘗試使用語音合成來解鎖
            const synth = window.speechSynthesis;
            if (synth) {
                // 使用空字符觸發語音合成初始化
                synth.cancel(); // 確保沒有待處理的語音
                const silence = new SpeechSynthesisUtterance('');
                silence.volume = 0.01; // 近乎無聲
                synth.speak(silence);
            }
            
            // 使用音頻標籤來解鎖
            const unlockAudio = new Audio();
            unlockAudio.src = "data:audio/mpeg;base64,SUQzBAAAAAABEVRYWFgAAAAtAAADY29tbWVudABCaWdTb3VuZEJhbmsuY29tIC8gTGFTb25vdGhlcXVlLm9yZwBURU5DAAAAHQAAA1N3aXRjaCBQbHVzIMKpIE5DSCBTb2Z0d2FyZQBUSVQyAAAABgAAAzIyMzUAVFNTRQAAAA8AAANMYXZmNTcuODMuMTAwAAAAAAAAAAAAAAD/80DEAAAAA0gAAAAATEFNRTMuMTAwVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/zQsRbAAADSAAAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/zQMSkAAADSAAAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV";
            await unlockAudio.play();
            
            console.log('音頻解鎖成功');
            
            // 隱藏解鎖界面
            document.getElementById('audioUnlockContainer').style.display = 'none';
            
            // 初始化虛擬助手
            window.virtualAssistant = new VirtualAssistant();
            
        } catch (error) {
            console.error('音頻解鎖失敗:', error);
            
            // 即使解鎖失敗也繼續初始化（可能沒有聲音）
            document.getElementById('audioUnlockContainer').style.display = 'none';
            
            window.virtualAssistant = new VirtualAssistant();
            alert('語音功能可能在此設備上不可用。請允許瀏覽器使用麥克風和揚聲器。');
        }
    });
});