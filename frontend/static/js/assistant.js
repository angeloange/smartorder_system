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
    // 修改 VirtualAssistant 類中的 speak 方法
    speak(text) {
        if (!text || text.trim() === '') return;
        
        // 首先添加消息到聊天窗口
        // 確保這行代碼被執行，無論語音是否成功
        if (!document.querySelector('.message.assistant:last-child .message-content')?.textContent?.includes(text)) {
            this.addMessage('assistant', text);
        }
        
        // 設置虛擬助手為說話狀態
        this.setAssistantState('speaking');
        
        // 使用 Azure 語音 API 生成語音
        fetch('/api/get_speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                text: text,
                style: 'female_warm'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 創建音頻元素並播放
                const audio = new Audio(data.audio_url);
                
                // 音頻結束時設置空閒狀態
                audio.onended = () => {
                    this.setAssistantState('idle');
                };
                
                // 音頻錯誤處理
                audio.onerror = (err) => {
                    console.error('音頻播放錯誤:', err);
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
                            this.setAssistantState('idle');
                        });
                    });
                }
            } else {
                console.error('語音生成失敗:', data.error);
                this.setAssistantState('idle');
            }
        })
        .catch(err => {
            console.error('無法連接到語音API:', err);
            this.setAssistantState('idle');
        });
    }
   // 添加移動設備上顯示播放按鈕的方法
showPlayButton(audioUrl) {
    const lastMessage = document.querySelector('.message.assistant:last-child');
    if (!lastMessage) return;
    
    // 檢查是否已有播放按鈕
    if (lastMessage.querySelector('.play-audio-btn')) return;
    
    // 創建播放按鈕
    const playButton = document.createElement('button');
    playButton.className = 'play-audio-btn';
    playButton.innerHTML = '<i class="fas fa-play-circle"></i> 播放語音';
    
    // 設置點擊事件
    playButton.addEventListener('click', () => {
        const audio = new Audio(audioUrl);
        audio.onplay = () => {
            this.isSpeaking = true;
            this.setAssistantState('speaking');
            playButton.innerHTML = '<i class="fas fa-volume-up"></i> 播放中...';
        };
        audio.onended = () => {
            this.isSpeaking = false;
            this.setAssistantState('idle');
            playButton.innerHTML = '<i class="fas fa-play-circle"></i> 重播語音';
        };
        audio.play().catch(console.error);
    });
    
    // 添加按鈕到消息元素
    lastMessage.appendChild(playButton);
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
// 修改 DOMContentLoaded 事件處理函數
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 載入完成，初始化虛擬助手...');
    
    // 檢查是否已經初始化
    if (window.virtualAssistant) {
        console.log('虛擬助手已初始化，跳過');
        return;
    }
    
    // 自動解鎖音頻，無需顯示按鈕
    const unlockContainer = document.getElementById('audioUnlockContainer');
    if (unlockContainer) {
        unlockContainer.style.display = 'none'; // 隱藏解鎖界面
    }
    
    // 嘗試自動解鎖音頻
    try {
        const autoUnlockAudio = async () => {
            // 使用現代音頻 API 自動解鎖
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const buffer = audioContext.createBuffer(1, 1, 22050);
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(0);
            
            // 使用語音合成自動解鎖
            const synth = window.speechSynthesis;
            if (synth) {
                synth.cancel();
                const silence = new SpeechSynthesisUtterance('');
                silence.volume = 0.01;
                synth.speak(silence);
            }
            
            console.log('音頻自動解鎖成功');
            
            // 初始化虛擬助手
            window.virtualAssistant = new VirtualAssistant();
        };
        
        // 執行自動解鎖
        autoUnlockAudio();
    } catch (error) {
        console.error('自動解鎖失敗:', error);
        // 即使失敗也初始化虛擬助手
        window.virtualAssistant = new VirtualAssistant();
    }
});

// 在 assistant.js 中添加檢測移動裝置並顯示解鎖按鈕
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

document.addEventListener('DOMContentLoaded', () => {
    // 如果是移動裝置，顯示解鎖按鈕
    if (isMobileDevice()) {
        const unlockDiv = document.createElement('div');
        unlockDiv.className = 'audio-unlock-container';
        unlockDiv.innerHTML = `
            <button class="unlock-button">
                <i class="fas fa-volume-up"></i> 點擊啟用語音
            </button>
        `;
        document.body.appendChild(unlockDiv);
        
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
            if (!window.virtualAssistant) {
                window.virtualAssistant = new VirtualAssistant();
            }
        });
        
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
    } else {
        // 電腦版保持原有行為
        if (!window.virtualAssistant) {
            window.virtualAssistant = new VirtualAssistant();
        }
    }
});