let currentOrderDetails = null;
let currentSpeechText = null;
let mediaRecorder = null;
let audioChunks = [];

document.addEventListener('DOMContentLoaded', function() {
    const startOrderBtn = document.getElementById('startOrder');
    const orderInput = document.getElementById('orderInput');
    const orderPrompt = document.getElementById('orderPrompt');
    const orderResult = document.getElementById('orderResult');
    const orderDetails = document.getElementById('orderDetails');
    const textModeBtn = document.getElementById('textModeBtn');
    const voiceModeBtn = document.getElementById('voiceModeBtn');
    const textInputMode = document.getElementById('textInputMode');
    const voiceInputMode = document.getElementById('voiceInputMode');
    const langToggle = document.getElementById('langToggle');
    let currentLang = 'zh-TW';
    let isVoiceMode = false;

    // 切換模式
    textModeBtn.onclick = () => {
        textModeBtn.classList.add('active');
        voiceModeBtn.classList.remove('active');
        textInputMode.classList.remove('hidden');
        voiceInputMode.classList.add('hidden');
        isVoiceMode = false;
        updateStatus('text');
    };

    voiceModeBtn.onclick = () => {
        voiceModeBtn.classList.add('active');
        textModeBtn.classList.remove('active');
        voiceInputMode.classList.remove('hidden');
        textInputMode.classList.add('hidden');
        isVoiceMode = true;
        updateStatus('voice');
    };

    function updateStatus(mode, status) {
        const voiceStatuses = {
            'preparing': '請稍候，正在準備錄音...',
            'recording': '請開始點餐（5秒）',
            'processing': '正在處理語音辨識...',
            'analyzing': '正在分析您的訂單...'
        };

        const textStatuses = {
            'processing': '正在處理您的訂單...',
            'analyzing': '正在分析您的訂單...'
        };

        orderPrompt.textContent = mode === 'voice' ? 
            voiceStatuses[status] || '請按下開始點餐按鈕' :
            textStatuses[status] || '請輸入您的訂單';
    }

    startOrderBtn.addEventListener('click', async function() {
        if (isVoiceMode) {
            try {
                this.disabled = true;
                orderPrompt.classList.remove('hidden');
                orderResult.classList.add('hidden');
                updateStatus('voice', 'preparing');
                
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                });

                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = async () => {
                    try {
                        updateStatus('voice', 'processing');
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob);

                        updateStatus('voice', 'analyzing');
                        const response = await fetch('/stop_recording', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        orderPrompt.classList.add('hidden');
                        
                        if (result.status === 'success') {
                            currentOrderDetails = result.order_details;
                            currentSpeechText = result.speech_text;
                            displayOrder(result.order_details, result.speech_text);
                        } else {
                            throw new Error(result.message);
                        }
                    } catch (error) {
                        console.error('處理音訊時發生錯誤:', error);
                        alert('處理音訊時發生錯誤，請稍後再試');
                    }
                };

                // 開始錄音
                mediaRecorder.start();
                updateStatus('voice', 'recording');
                
                // 5秒後停止錄音
                setTimeout(() => {
                    if (mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        stream.getTracks().forEach(track => track.stop());
                    }
                }, 5000);

            } catch (error) {
                console.error('錄音失敗:', error);
                orderPrompt.classList.add('hidden');
                this.disabled = false;
            }
        } else {
            // 文字輸入模式
            if (!orderInput.value.trim()) {
                alert('請輸入您的訂單');
                return;
            }

            try {
                this.disabled = true;
                orderPrompt.classList.remove('hidden');
                orderResult.classList.add('hidden');
                
                console.log('發送文字訂單:', orderInput.value); // 除錯用
                
                const response = await fetch('/analyze_text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        text: orderInput.value 
                    })
                });
                
                console.log('收到回應'); // 除錯用
                
                const result = await response.json();
                console.log('處理結果:', result); // 除錯用
                
                if (result.status === 'success') {
                    currentOrderDetails = result.order_details;
                    currentSpeechText = orderInput.value;
                    displayOrder(result.order_details, currentSpeechText);
                    orderPrompt.classList.add('hidden');
                    orderResult.classList.remove('hidden');
                } else {
                    throw new Error(result.message || '處理失敗');
                }

            } catch (error) {
                console.error('處理訂單時發生錯誤:', error);
                alert('處理訂單時發生錯誤，請稍後再試');
            } finally {
                this.disabled = false;
                orderPrompt.classList.add('hidden');
            }
        }
    });

    // 確認訂單按鈕
    document.getElementById('confirmOrder').onclick = async () => {
        try {
            const response = await fetch('/confirm_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_details: currentOrderDetails,
                    speech_text: currentSpeechText
                })
            });
            
            const result = await response.json();
            if (result.status === 'success') {
                orderDetails.innerHTML = '<div class="success-message">好的，尊貴的客人請稍候，正在為您製作飲品</div>';
                document.querySelector('.button-group').classList.add('hidden');
                
                // 5秒後重置
                setTimeout(() => {
                    orderResult.classList.add('hidden');
                    startOrderBtn.disabled = false;
                    orderInput.value = '';
                }, 5000);
            }
        } catch (error) {
            console.error('確認訂單時發生錯誤:', error);
        }
    };

    // 取消按鈕
    document.getElementById('cancelOrder').onclick = () => {
        orderResult.classList.add('hidden');
        startOrderBtn.disabled = false;
        orderInput.value = '';
    };

    // 立即更新熱銷排行
    updateTopDrinks();
    // 每5分鐘更新一次
    setInterval(updateTopDrinks, 300000);

    // 綁定語言切換事件
    langToggle.onchange = function() {
        currentLang = this.checked ? 'en' : 'zh-TW';
        updateTranslations(currentLang);
    };

    // 在 DOMContentLoaded 的最後呼叫初始化
    updateTranslations(currentLang);
});

async function updateTopDrinks() {
    try {
        console.log('開始更新熱銷飲料');  // 除錯用
        const response = await fetch('/monthly_top_drinks');
        const result = await response.json();
        
        console.log('API 回應:', result);  // 除錯用
        
        if (result.status === 'success' && result.data.length > 0) {
            const topDrinksContainer = document.querySelector('.rank-list.hot-sales');            if (topDrinksContainer) {
                topDrinksContainer.innerHTML = result.data
                    .map((item, index) => `
                        <div class="rank-item">
                            ${index + 1}. ${item.drink_name} (${item.count}杯)
                        </div>
                    `).join('');
            } else {
                console.error('找不到熱銷排行容器(.hot-sales)');
            }
        } else {
            console.log('沒有熱銷資料或獲取失敗');
        }
    } catch (error) {
        console.error('更新熱銷飲料失敗:', error);
    }
}

function displayOrder(orderDetails, speechText) {
    const container = document.getElementById('orderDetails');
    container.innerHTML = '';
    
    orderDetails.forEach(item => {
        const orderItem = document.createElement('div');
        orderItem.classList.add('order-item');
        
        // 格式化顯示
        const sizeTxt = item.size || '中杯';
        const quantity = item.quantity || 1;
        const iceTxt = formatIceType(item.ice);
        const sugarTxt = formatSugarType(item.sugar);
        
        orderItem.innerHTML = `
            <div class="item-name">
                ${item.drink_name}(${sizeTxt}) x${quantity}
            </div>
            <div class="item-options">
                (${sugarTxt}, ${iceTxt})
            </div>
        `;
        container.appendChild(orderItem);
    });
    
    document.getElementById('orderResult').classList.remove('hidden');
}

// 格式化冰塊選項
function formatIceType(ice) {
    const iceMap = {
        'iced': '正常冰',
        'hot': '熱飲',
        'room_temp': '常溫'
    };
    return iceMap[ice] || ice;
}

// 格式化糖度選項
function formatSugarType(sugar) {
    const sugarMap = {
        'full': '全糖',
        'half': '半糖',
        'free': '無糖'
    };
    return sugarMap[sugar] || sugar;
}


// 更新所有翻譯的函數
function updateTranslations(lang) {
    // 更新所有帶有 data-translate 屬性的元素
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        if (translations[lang][key]) {
            if (element.tagName === 'INPUT') {
                element.placeholder = translations[lang][key];
            } else {
                element.textContent = translations[lang][key];
            }
        }
    });

    // 更新菜單項目
    document.querySelectorAll('.item').forEach(item => {
        const drinkKey = item.getAttribute('data-drink-key');
        if (drinkKey) {
            const nameElement = item.querySelector('.name');
            const priceElement = item.querySelector('.price');
            
            if (nameElement && translations[lang].drinks[drinkKey]) {
                nameElement.textContent = translations[lang].drinks[drinkKey];
            }
            
            if (priceElement) {
                const price = priceElement.getAttribute('data-price');
                priceElement.textContent = `${price}${translations[lang].currency}`;
            }
        }
    });

    // 更新熱銷排行的顯示格式
    const hotSaleItems = document.querySelectorAll('.rank-item');
    hotSaleItems.forEach(item => {
        const count = item.getAttribute('data-count');
        if (count) {
            const drinkName = item.getAttribute('data-drink-key');
            if (drinkName && translations[lang].drinks[drinkName]) {
                item.textContent = `${translations[lang].drinks[drinkName]} (${count}${translations[lang].unit})`;
            }
        }
    });

    // 更新菜單分類標題
    document.querySelectorAll('.category h3').forEach(header => {
        const category = header.closest('.category');
        if (category) {
            const categoryType = category.getAttribute('data-category');
            if (categoryType) {
                header.textContent = translations[lang][`${categoryType}Section`];
            }
        }
    });

    // 更新價格單位
    document.querySelectorAll('.price').forEach(price => {
        const priceValue = price.getAttribute('data-price');
        if (priceValue) {
            price.textContent = `${priceValue}${translations[lang].currency}`;
        }
    });

    // 更新狀態訊息
    const orderPrompt = document.getElementById('orderPrompt');
    if (orderPrompt && orderPrompt.textContent) {
        updateStatus(isVoiceMode ? 'voice' : 'text');
    }

    // 更新語音提示
    const voiceStatus = document.querySelector('.voice-status');
    if (voiceStatus) {
        voiceStatus.textContent = translations[lang].voicePrompt;
    }
}