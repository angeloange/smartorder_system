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
    const waitingTimeElement = document.querySelector('.waiting-time');
    const virtualAssistant = window.assistant || {
        addMessage: function(type, text) {
            console.log(`[菜單] ${type}: ${text}`);
        }
    };
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

    // 初始化 WebSocket 連接
    const socket = io(window.location.hostname + ':5003');    
    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
        // 連接後獲取初始等候時間
        fetchWaitingTime();
    });
    
    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
    });
    
    // 監聽訂單完成事件
    socket.on('order_completed', (data) => {
        console.log('訂單完成:', data);
        const numberDisplay = document.querySelector('.number-display');
        if (numberDisplay) {
            numberDisplay.textContent = data.order_number;
            // 添加閃爍效果
            numberDisplay.classList.add('flash');
            setTimeout(() => {
                numberDisplay.classList.remove('flash');
            }, 2000);
        }
        
        // 更新等候時間
        if (waitingTimeElement && data.waiting_time !== undefined) {
            updateWaitingTime(data.waiting_time);
        }
    });

    // 接收等候時間更新事件
    socket.on('waiting_time_update', (data) => {
        console.log('Waiting time update:', data);
        if (waitingTimeElement && data.waiting_time !== undefined) {
            updateWaitingTime(data.waiting_time);
        }
    });

    // 更新等候時間顯示
    function updateWaitingTime(minutes) {
        waitingTimeElement.textContent = `${minutes} 分鐘`;
        // 添加動畫效果
        waitingTimeElement.classList.add('flash');
        setTimeout(() => {
            waitingTimeElement.classList.remove('flash');
        }, 2000);
    }

    // 獲取初始等候時間
    function fetchWaitingTime() {
        fetch('http://localhost:5003/api/waiting-time')
            .then(response => response.json())
            .then(data => {
                if (data.waiting_time !== undefined) {
                    updateWaitingTime(data.waiting_time);
                }
            })
            .catch(error => console.error('Error fetching waiting time:', error));
    }

    // 確認訂單按鈕
    // 修改確認訂單按鈕的處理函數
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
                // 使用 SweetAlert2 顯示成功訊息
                Swal.fire({
                    title: '訂單已確認',
                    html: `
                        <p>好的，尊貴的客人請稍候</p>
                        <p>正在為您製作飲品</p>
                        <p>您的取餐號碼是 <strong>${result.order_number}</strong></p>
                    `,
                    icon: 'success',
                    timer: 3000,
                    timerProgressBar: true,
                    showConfirmButton: false
                }).then(() => {
                    // 3秒後重置頁面
                    location.reload();
                });
            } else {
                throw new Error(result.message || '訂單處理失敗');
            }
        } catch (error) {
            console.error('確認訂單時發生錯誤:', error);
            Swal.fire({
                title: '錯誤',
                text: '訂單處理失敗，請稍後再試',
                icon: 'error',
                confirmButtonText: '確定'
            });
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

    // 調用更新熱銷排行
    console.log('從 menu.js 主要初始化中調用 updateTopDrinks');
    updateTopDrinks();

    // 在菜單卡片上添加點擊事件
    initializeMenuCards();
});

async function updateTopDrinks() {
    try {
        console.log('開始更新熱銷飲料');
        const response = await fetch('/monthly_top_drinks');
        const result = await response.json();
        
        console.log('熱銷API回應:', result);
        
        if (result.status === 'success' && result.data && result.data.length > 0) {
            const topDrinksContainer = document.querySelector('.rank-list.hot-sales');
            if (topDrinksContainer) {
                // 清空容器
                topDrinksContainer.innerHTML = '';
                
                // 建立排行項目
                result.data.forEach((item, index) => {
                    const rankItem = document.createElement('div');
                    rankItem.className = 'rank-item';
                    rankItem.textContent = `${index + 1}. ${item.name || '未知飲品'} (${item.count || 0}杯)`;
                    
                    topDrinksContainer.appendChild(rankItem);
                });
            } else {
                console.error('找不到熱銷排行容器(.hot-sales)');
            }
        } else {
            const container = document.querySelector('.rank-list.hot-sales');
            if (container) {
                container.innerHTML = '<div class="rank-item">暫無熱銷資料</div>';
            }
            console.log('沒有熱銷資料或獲取失敗');
        }
    } catch (error) {
        console.error('更新熱銷飲料失敗:', error);
        const container = document.querySelector('.rank-list.hot-sales');
        if (container) {
            container.innerHTML = '<div class="rank-item">資料載入失敗</div>';
        }
    }
}

async function updateWeatherRecommendations() {
    try {
        console.log('開始更新天氣推薦菜單');
        
        // 向 API 發送請求
        const response = await fetch('/api/weather_recommend'); 
        const result = await response.json();
        
        console.log('天氣推薦API回應:', result);
        
        if (result && result.length >= 6) {
            const weatherContainer = document.querySelector('.rank-list.weather-recommend');
            if (weatherContainer) {
                weatherContainer.innerHTML = '';  // 清空原本內容

                // 取第 4~6 名的飲料
                const selectedDrinks = result?.slice(3, 6) || [];

                selectedDrinks.forEach((drink, index) => {
                    const rankItem = document.createElement('div');
                    rankItem.className = 'rank-item';
                    rankItem.textContent = `${index + 1}. ${drink}`;

                    weatherContainer.appendChild(rankItem);
                });
            } else {
                console.error('找不到天氣推薦排行容器(.weather-recommend)');
            }
        } else {
            const container = document.querySelector('.rank-list.weather-recommend');
            if (container) {
                container.innerHTML = '<div class="rank-item">暫無天氣推薦資料</div>';
            }
            console.log('天氣推薦資料不足或獲取失敗');
        }
    } catch (error) {
        console.error('更新天氣推薦菜單失敗:', error);
        const container = document.querySelector('.rank-list.weather-recommend');
        if (container) {
            container.innerHTML = '<div class="rank-item">資料載入失敗</div>';
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    updateWeatherRecommendations();
    setInterval(updateWeatherRecommendations, 30 * 60 * 1000);  // 30 分鐘更新一次
});

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
// 修改 initializeMenuCards() 函數的選擇器
function initializeMenuCards() {
    console.log('初始化菜單點擊事件');
    
    // 修改選擇器，使用更精確的定位
    const menuItems = document.querySelectorAll('.menu-grid .item');
    console.log(`找到 ${menuItems.length} 個菜單項目`);
    
    menuItems.forEach(item => {
        item.style.cursor = 'pointer';
        
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 從元素中獲取飲料名稱
            const nameElement = this.querySelector('.name');
            if (!nameElement) {
                console.log('找不到飲料名稱元素');
                return;
            }
            
            const drinkName = nameElement.textContent.trim();
            console.log(`點擊了飲料: ${drinkName}`);  // 偵錯用
            
            // 尋找文字輸入框
            const chatInput = document.getElementById('chatInput');
            if (!chatInput) {
                console.log('找不到輸入框元素');
                return;
            }
            
            // 智能更新輸入框文字
            const currentText = chatInput.value.trim();
            if (currentText) {
                chatInput.value = `${currentText}，再來一杯${drinkName}`;
            } else {
                chatInput.value = `我要一杯${drinkName}`;
            }
            
            // 聚焦輸入框
            chatInput.focus();
            
            // 增加點擊視覺反饋
            this.classList.add('selected');
            setTimeout(() => {
                this.classList.remove('selected');
            }, 200);
        });
    });
}

// 確保在 DOM 完全載入後才初始化
document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
    
    // 初始化菜單點擊
    initializeMenuCards();
    
    // 監聽動態載入的內容
    const menuContainer = document.querySelector('.menu-container');
    if (menuContainer) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    initializeMenuCards();
                }
            });
        });
        
        observer.observe(menuContainer, {
            childList: true,
            subtree: true
        });
    }
});