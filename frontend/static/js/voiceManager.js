/**
 * 語音管理器 - 使用 Azure 語音服務處理文字轉語音
 */
(function() {
    // 避免重複初始化
    if (window.voiceManager && window.voiceManager.initialized) return;
    
    console.log('載入 Azure Speech SDK...');
    
    // 基本語音管理器
    const voiceManager = {
        synthesizer: null,
        speechConfig: null, // 添加speechConfig屬性
        initialized: false,
        speaking: false,
        callbacks: {},
        
        // 初始化 Azure 語音服務
        init: function(subscriptionKey, region) {
            if (this.initialized) return true;
            
            if (!subscriptionKey || !region) {
                console.warn('未提供 Azure 語音服務憑證');
                return false;
            }
            
            try {
                // 檢查 SDK 是否加載
                if (typeof SpeechSDK === 'undefined') {
                    console.error('Speech SDK 未載入，請確認 Azure Speech SDK 腳本已正確添加到頁面');
                    return false;
                }
                
                // 釋放之前的合成器資源（如果有）
                if (this.synthesizer) {
                    try {
                        this.synthesizer.close();
                    } catch (e) {
                        console.warn('關閉舊語音合成器時出錯:', e);
                    }
                }
                
                // 建立語音設置並保存為類屬性
                this.speechConfig = SpeechSDK.SpeechConfig.fromSubscription(subscriptionKey, region);
                this.speechConfig.speechSynthesisVoiceName = "zh-TW-HsiaoChenNeural"; // 台灣女性語音
                
                // 建立音頻設置
                const audioConfig = SpeechSDK.AudioConfig.fromDefaultSpeakerOutput();
                
                // 建立合成器
                this.synthesizer = new SpeechSDK.SpeechSynthesizer(this.speechConfig, audioConfig);
                this.initialized = true;
                
                console.log('Azure 語音配置初始化完成 ✓');
                return true;
            } catch (error) {
                console.error('初始化語音服務失敗:', error);
                return false;
            }
        },
        
        // 修改 speak 函數部分
        speak: function(text) {
            if (!text || text.trim() === '') {
                console.warn('沒有有效的文字內容需要播放');
                return false;
            }
            
            if (!this.synthesizer || !this.speechConfig) {
                console.warn('語音合成器尚未初始化，嘗試重新初始化');
                
                // 如果已獲取過憑證，嘗試重新初始化
                if (this.lastCredentials) {
                    this.init(this.lastCredentials.key, this.lastCredentials.region);
                } else {
                    this.fetchCredentialsAndInit();
                    return false;
                }
                
                // 如果初始化失敗
                if (!this.synthesizer || !this.speechConfig) {
                    console.error('初始化失敗，無法播放語音');
                    return false;
                }
            }
            
            try {
                // 開始播放前日誌
                console.log('開始播放語音:', text);
                this.speaking = true;
                
                // 檢查系統音量並播放測試音頻
                this.playTestTone(0.05, 100);
                
                // 通知開始說話
                if (this.callbacks.onSpeakStart) {
                    this.callbacks.onSpeakStart();
                }
                
                // 使用增強音量的 SSML
                const ssml = `
                    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-TW">
                        <voice name="zh-TW-HsiaoChenNeural">
                            <prosody rate="+10%" volume="+100%">${text}</prosody>
                        </voice>
                    </speak>
                `;
                
                // 直接使用已初始化的合成器
                this.synthesizer.speakSsmlAsync(
                    ssml,
                    result => {
                        this.speaking = false;
                        console.log('語音播放完成:', result.reason);
                        
                        if (this.callbacks.onSpeakEnd) {
                            this.callbacks.onSpeakEnd();
                        }
                    },
                    error => {
                        this.speaking = false;
                        console.error('語音播放失敗:', error);
                        
                        if (this.callbacks.onSpeakEnd) {
                            this.callbacks.onSpeakEnd();
                        }
                    }
                );
                return true;
            } catch (error) {
                this.speaking = false;
                console.error('語音播放過程中出錯:', error);
                
                if (this.callbacks.onSpeakEnd) {
                    this.callbacks.onSpeakEnd();
                }
                return false;
            }
        },
        
        // 添加測試音頻函數
        playTestTone: function(volume, duration) {
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                gainNode.gain.value = volume; // 音量控制
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                oscillator.frequency.value = 440; // A4音符
                oscillator.start();
                setTimeout(() => {
                    oscillator.stop();
                    audioContext.close().catch(e => console.log('關閉音頻上下文出錯:', e));
                }, duration);
                return true;
            } catch (e) {
                console.warn('播放測試音頻失敗:', e);
                return false;
            }
        },
        
        // 直接從伺服器獲取憑證並初始化
        fetchCredentialsAndInit: function() {
            console.log('從伺服器獲取 Azure 憑證...');
            
            fetch('/azure_credentials')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`伺服器返回錯誤: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('收到 Azure 憑證回應:', data);
                
                if (data.key && data.region) {
                    // 保存憑證以備重新初始化時使用
                    this.lastCredentials = {
                        key: data.key,
                        region: data.region
                    };
                    
                    // 初始化語音服務
                    const success = this.init(data.key, data.region);
                    console.log('Azure 語音服務初始化' + (success ? '成功 ✓' : '失敗 ✗'));
                } else {
                    console.error('未獲取到有效的 Azure 語音憑證');
                }
            })
            .catch(error => {
                console.error('獲取或處理 Azure 憑證時出錯:', error);
            });
        }, // 添加了缺少的逗號
        
        // 註冊回調函數
        registerCallbacks: function(callbacks) {
            this.callbacks = callbacks || {};
        }
    };
    
    // 設置全局訪問
    window.voiceManager = voiceManager;
    
    // 當頁面完全加載後初始化語音服務
    document.addEventListener('DOMContentLoaded', function() {
        console.log('頁面加載完成，準備初始化 Azure 語音服務...');
        
        // 先測試音頻系統
        voiceManager.playTestTone(0.1, 200);
        
        // 然後初始化語音服務
        setTimeout(() => {
            voiceManager.fetchCredentialsAndInit();
        }, 300);
    });
})();