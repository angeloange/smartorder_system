/**
 * 語音管理器 - 使用 Azure 語音服務處理文字轉語音
 */
(function() {
    // 避免重複初始化
    if (window.voiceManager) return;
    
    console.log('載入 Azure Speech SDK...');
    
    // 基本語音管理器
    const voiceManager = {
        synthesizer: null,
        speaking: false,
        callbacks: {},
        
        // 初始化 Azure 語音服務
        init: function(subscriptionKey, region) {
            if (!subscriptionKey || !region) {
                console.warn('未提供 Azure 語音服務憑證');
                return false;
            }
            
            try {
                if (!window.SpeechSDK) {
                    console.error('Speech SDK 未載入');
                    return false;
                }
                
                const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(subscriptionKey, region);
                speechConfig.speechSynthesisVoiceName = "zh-TW-HsiaoChenNeural"; // 使用台灣女性語音
                this.synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig);
                console.log('Azure 語音配置初始化完成');
                return true;
            } catch (error) {
                console.error('初始化語音服務失敗:', error);
                return false;
            }
        },
        
        // 語音播放函數
        speak: function(text) {
            if (!this.synthesizer) {
                console.warn('語音合成器尚未初始化');
                return false;
            }
            
            try {
                this.speaking = true;
                console.log('播放語音:', text);
                
                // 使用 SSML 格式設置語音速度
                const ssml = `
                    <speak version="1.2" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-TW">
                        <voice name="zh-TW-HsiaoChenNeural">
                            <prosody rate="+30%">${text}</prosody>
                        </voice>
                    </speak>
                `;
                
                // 通知開始說話
                if (this.callbacks.onSpeakStart) {
                    this.callbacks.onSpeakStart();
                }
                
                // 使用 speakSsmlAsync 而不是 speakTextAsync
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
                console.error('語音播放失敗:', error);
                
                if (this.callbacks.onSpeakEnd) {
                    this.callbacks.onSpeakEnd();
                }
                return false;
            }
        },
        
        // 註冊回調函數
        registerCallbacks: function(callbacks) {
            this.callbacks = callbacks || {};
        }
    };
    
    // 設置全局訪問
    window.voiceManager = voiceManager;
    
    console.log('Azure Speech SDK 載入完成');
    
    // 修改 DOMContentLoaded 事件處理程序
    document.addEventListener('DOMContentLoaded', function() {
        console.log('初始化 Azure 語音配置...');
        
        // 從後端獲取 Azure 憑證
        fetch('/azure_credentials')
        .then(response => response.json())
        .then(data => {
            console.log('收到 Azure 憑證回應，憑證是否存在:', !!data.key);
            
            if (data.key && data.key.length > 10) {
                console.log('初始化 Azure 語音服務，區域:', data.region);
                voiceManager.init(data.key, data.region);
            } else {
                console.error('未獲取到有效的 Azure 語音憑證');
                // 不要使用無效的硬編碼密鑰
                // 這裡什麼都不做，而不是使用無效的密鑰
            }
        })
        .catch(error => {
            console.error('獲取 Azure 憑證失敗:', error);
            // 不要使用無效的硬編碼密鑰
        });
    });
}
)();