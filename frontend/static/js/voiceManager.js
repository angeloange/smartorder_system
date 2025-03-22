/**
 * 語音管理模組 - 使用 Azure 語音服務
 */
class VoiceManager {
    constructor() {
        // Azure 語音服務設置
        this.azureConfig = {
            key: 'a2dde9e0bfda4a4f968b0dfd27e1b2a2',
            region: 'eastasia',
            speechRecognitionLang: 'zh-TW',
            speechSynthesisLang: 'zh-TW',
            speechSynthesisVoice: 'zh-TW-HsiaoChenNeural'
        };
        
        // 狀態追蹤
        this.isSpeaking = false;
        this.isListening = false;
        
        // 回調函數
        this.callbacks = {
            onSpeakStart: null,
            onSpeakEnd: null,
            onSpeechStart: null,
            onSpeechEnd: null,
            onSpeechResult: null,
            onSpeechError: null
        };
        
        // 初始化 Azure SDK
        this.loadAzureSDK();
    }
    
    /**
     * 載入 Azure Speech SDK
     */
    loadAzureSDK() {
        // 檢查 SDK 是否已經載入
        if (window.SpeechSDK) {
            this.initSpeechConfig();
            return;
        }
        
        // 動態載入 SDK
        console.log('載入 Azure Speech SDK...');
        const script = document.createElement('script');
        script.src = 'https://aka.ms/csspeech/jsbrowserpackageraw';
        script.async = true;
        script.onload = () => {
            console.log('Azure Speech SDK 載入完成');
            this.initSpeechConfig();
        };
        script.onerror = (err) => {
            console.error('Azure Speech SDK 載入失敗:', err);
        };
        
        document.head.appendChild(script);
    }
    
    /**
     * 初始化語音配置
     */
    initSpeechConfig() {
        if (!window.SpeechSDK) {
            console.error('Azure Speech SDK 未載入');
            return;
        }
        
        try {
            console.log('初始化 Azure 語音配置...');
            
            // 創建語音配置
            this.speechConfig = window.SpeechSDK.SpeechConfig.fromSubscription(
                this.azureConfig.key, 
                this.azureConfig.region
            );
            
            // 設置語音識別和合成語言
            this.speechConfig.speechRecognitionLanguage = this.azureConfig.speechRecognitionLang;
            this.speechConfig.speechSynthesisLanguage = this.azureConfig.speechSynthesisLang;
            this.speechConfig.speechSynthesisVoiceName = this.azureConfig.speechSynthesisVoice;
            
            console.log('Azure 語音配置初始化完成');
        } catch (error) {
            console.error('初始化語音配置失敗:', error);
        }
    }
    
    /**
     * 註冊回調函數
     * @param {Object} callbacks 回調函數物件
     */
    registerCallbacks(callbacks) {
        this.callbacks = {...this.callbacks, ...callbacks};
    }
    
    /**
     * 語音合成 - 文字轉語音
     * @param {string} text 要轉換的文字
     */
    speak(text) {
        if (!text || text.trim() === '') return;
        
        // 檢查 SDK 是否已加載
        if (!window.SpeechSDK || !this.speechConfig) {
            console.log('Azure SDK 未準備好，使用瀏覽器語音合成...');
            this.speakWithBrowser(text);
            return;
        }
        
        try {
            // 通知開始說話
            if (this.callbacks.onSpeakStart) {
                this.callbacks.onSpeakStart();
            }
            
            this.isSpeaking = true;
            
            // 取消之前的語音
            if (this.synthesizer) {
                this.synthesizer.close();
            }
            
            // 創建音頻配置和合成器
            const audioConfig = window.SpeechSDK.AudioConfig.fromDefaultSpeakerOutput();
            this.synthesizer = new window.SpeechSDK.SpeechSynthesizer(
                this.speechConfig, 
                audioConfig
            );
            
            // 使用 SSML 格式合成語音
            const ssml = this.generateSSML(text);
            
            console.log('開始播放語音...');
            this.synthesizer.speakSsmlAsync(
                ssml,
                result => {
                    if (result.reason === window.SpeechSDK.ResultReason.SynthesizingAudioCompleted) {
                        console.log('語音播放完成');
                    } else {
                        console.error('語音合成失敗:', result.errorDetails);
                    }
                    
                    this.isSpeaking = false;
                    if (this.callbacks.onSpeakEnd) {
                        this.callbacks.onSpeakEnd();
                    }
                    
                    this.synthesizer.close();
                    this.synthesizer = null;
                },
                error => {
                    console.error('語音合成錯誤:', error);
                    this.isSpeaking = false;
                    
                    if (this.callbacks.onSpeakEnd) {
                        this.callbacks.onSpeakEnd();
                    }
                    
                    // 嘗試使用瀏覽器合成作為備用
                    this.speakWithBrowser(text);
                    
                    if (this.synthesizer) {
                        this.synthesizer.close();
                        this.synthesizer = null;
                    }
                }
            );
        } catch (error) {
            console.error('語音合成發生錯誤:', error);
            this.isSpeaking = false;
            
            if (this.callbacks.onSpeakEnd) {
                this.callbacks.onSpeakEnd();
            }
            
            // 嘗試使用瀏覽器合成作為備用
            this.speakWithBrowser(text);
        }
    }
    
    /**
     * 使用瀏覽器內置語音合成 (備用方案)
     * @param {string} text 要轉換的文字
     */
    speakWithBrowser(text) {
        if (window.speechSynthesis) {
            try {
                if (this.callbacks.onSpeakStart) {
                    this.callbacks.onSpeakStart();
                }
                
                // 取消正在播放的語音
                window.speechSynthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'zh-TW';
                
                // 找到合適的中文語音
                const voices = window.speechSynthesis.getVoices();
                const chineseVoice = voices.find(v => 
                    v.lang === 'zh-TW' || 
                    v.lang === 'zh-HK' || 
                    v.lang === 'zh-CN'
                );
                
                if (chineseVoice) {
                    utterance.voice = chineseVoice;
                }
                
                utterance.onend = () => {
                    if (this.callbacks.onSpeakEnd) {
                        this.callbacks.onSpeakEnd();
                    }
                };
                
                utterance.onerror = (err) => {
                    console.error('瀏覽器語音合成錯誤:', err);
                    if (this.callbacks.onSpeakEnd) {
                        this.callbacks.onSpeakEnd();
                    }
                };
                
                window.speechSynthesis.speak(utterance);
            } catch (error) {
                console.error('瀏覽器語音合成出錯:', error);
                if (this.callbacks.onSpeakEnd) {
                    this.callbacks.onSpeakEnd();
                }
            }
        } else {
            console.warn('瀏覽器不支持語音合成');
            if (this.callbacks.onSpeakEnd) {
                this.callbacks.onSpeakEnd();
            }
        }
    }
    
    /**
     * 生成 SSML 格式文本
     * @param {string} text 原始文本
     * @return {string} SSML 格式文本
     */
    generateSSML(text) {
        // 處理特殊字符
        text = text.replace(/&/g, '&amp;')
                   .replace(/</g, '&lt;')
                   .replace(/>/g, '&gt;')
                   .replace(/"/g, '&quot;')
                   .replace(/'/g, '&apos;');
        
        // 創建 SSML 文檔
        return `
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="${this.azureConfig.speechSynthesisLang}">
                <voice name="${this.azureConfig.speechSynthesisVoice}">
                    <prosody rate="1.0" pitch="0">
                        ${text}
                    </prosody>
                </voice>
            </speak>
        `;
    }
    
    /**
     * 開始語音識別
     */
    startVoiceInput() {
        if (this.isListening) return;
        
        // 檢查 SDK 是否已加載
        if (!window.SpeechSDK || !this.speechConfig) {
            console.log('Azure SDK 未準備好，使用瀏覽器語音識別...');
            this.startBrowserVoiceInput();
            return;
        }
        
        try {
            // 創建音頻配置
            const audioConfig = window.SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
            
            // 創建語音識別器
            this.recognizer = new window.SpeechSDK.SpeechRecognizer(
                this.speechConfig, 
                audioConfig
            );
            
            // 設置狀態並通知開始識別
            this.isListening = true;
            if (this.callbacks.onSpeechStart) {
                this.callbacks.onSpeechStart();
            }
            
            console.log('開始語音識別...');
            
            // 設定超時
            const timeout = setTimeout(() => {
                if (this.isListening) {
                    console.warn('語音識別超時');
                    this.stopVoiceInput();
                    
                    if (this.callbacks.onSpeechError) {
                        this.callbacks.onSpeechError('timeout');
                    }
                }
            }, 8000);
            
            // 開始識別
            this.recognizer.recognizeOnceAsync(
                result => {
                    clearTimeout(timeout);
                    
                    if (result.reason === window.SpeechSDK.ResultReason.RecognizedSpeech) {
                        const transcript = result.text;
                        console.log('識別結果:', transcript);
                        
                        if (this.callbacks.onSpeechResult) {
                            this.callbacks.onSpeechResult(transcript);
                        }
                    } else {
                        console.error('識別失敗:', result);
                        
                        if (this.callbacks.onSpeechError) {
                            this.callbacks.onSpeechError('no_speech');
                        }
                    }
                    
                    this.isListening = false;
                    if (this.callbacks.onSpeechEnd) {
                        this.callbacks.onSpeechEnd();
                    }
                    
                    this.recognizer.close();
                    this.recognizer = null;
                },
                error => {
                    clearTimeout(timeout);
                    console.error('語音識別錯誤:', error);
                    
                    this.isListening = false;
                    if (this.callbacks.onSpeechError) {
                        this.callbacks.onSpeechError('error');
                    }
                    
                    if (this.callbacks.onSpeechEnd) {
                        this.callbacks.onSpeechEnd();
                    }
                    
                    if (this.recognizer) {
                        this.recognizer.close();
                        this.recognizer = null;
                    }
                }
            );
        } catch (error) {
            console.error('啟動語音識別時出錯:', error);
            this.isListening = false;
            
            if (this.callbacks.onSpeechError) {
                this.callbacks.onSpeechError('start_error');
            }
            
            if (this.callbacks.onSpeechEnd) {
                this.callbacks.onSpeechEnd();
            }
            
            // 嘗試使用瀏覽器語音識別作為備用
            this.startBrowserVoiceInput();
        }
    }
    
    /**
     * 使用瀏覽器語音識別 (備用方案)
     */
    startBrowserVoiceInput() {
        // 檢查瀏覽器是否支持語音識別
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.error('瀏覽器不支持語音識別');
            
            if (this.callbacks.onSpeechError) {
                this.callbacks.onSpeechError('not_supported');
            }
            
            return;
        }
        
        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.browserRecognizer = new SpeechRecognition();
            
            this.browserRecognizer.lang = 'zh-TW';
            this.browserRecognizer.continuous = false;
            this.browserRecognizer.interimResults = false;
            
            this.browserRecognizer.onstart = () => {
                this.isListening = true;
                if (this.callbacks.onSpeechStart) {
                    this.callbacks.onSpeechStart();
                }
            };
            
            this.browserRecognizer.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('瀏覽器語音識別結果:', transcript);
                
                if (this.callbacks.onSpeechResult) {
                    this.callbacks.onSpeechResult(transcript);
                }
            };
            
            this.browserRecognizer.onerror = (event) => {
                console.error('瀏覽器語音識別錯誤:', event.error);
                
                if (this.callbacks.onSpeechError) {
                    this.callbacks.onSpeechError(event.error);
                }
            };
            
            this.browserRecognizer.onend = () => {
                this.isListening = false;
                if (this.callbacks.onSpeechEnd) {
                    this.callbacks.onSpeechEnd();
                }
            };
            
            this.browserRecognizer.start();
        } catch (error) {
            console.error('啟動瀏覽器語音識別時出錯:', error);
            this.isListening = false;
            
            if (this.callbacks.onSpeechError) {
                this.callbacks.onSpeechError('start_error');
            }
            
            if (this.callbacks.onSpeechEnd) {
                this.callbacks.onSpeechEnd();
            }
        }
    }
    
    /**
     * 停止語音識別
     */
    stopVoiceInput() {
        if (!this.isListening) return;
        
        if (this.recognizer) {
            this.recognizer.stopContinuousRecognitionAsync(
                () => {
                    this.isListening = false;
                    if (this.callbacks.onSpeechEnd) {
                        this.callbacks.onSpeechEnd();
                    }
                    
                    this.recognizer.close();
                    this.recognizer = null;
                },
                (error) => {
                    console.error('停止語音識別出錯:', error);
                    this.isListening = false;
                    
                    if (this.callbacks.onSpeechEnd) {
                        this.callbacks.onSpeechEnd();
                    }
                    
                    this.recognizer.close();
                    this.recognizer = null;
                }
            );
        } else if (this.browserRecognizer) {
            try {
                this.browserRecognizer.stop();
            } catch (error) {
                console.error('停止瀏覽器語音識別出錯:', error);
            }
            
            this.isListening = false;
            if (this.callbacks.onSpeechEnd) {
                this.callbacks.onSpeechEnd();
            }
        }
    }
    
    /**
     * 切換語音識別狀態
     */
    toggleVoiceInput() {
        if (this.isListening) {
            this.stopVoiceInput();
        } else {
            this.startVoiceInput();
        }
    }
}

// 導出為全局單例
window.voiceManager = new VoiceManager();
export default window.voiceManager;
