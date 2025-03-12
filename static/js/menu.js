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
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    updateStatus('voice', 'processing');
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const formData = new FormData();
                    formData.append('audio', audioBlob);

                    try {
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
                        }
                    } catch (error) {
                        console.error('處理音訊時發生錯誤:', error);
                    }
                };

                // 延遲開始錄音，給予使用者準備時間
                setTimeout(() => {
                    mediaRecorder.start();
                    updateStatus('voice', 'recording');
                    
                    setTimeout(() => {
                        if (mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();
                            stream.getTracks().forEach(track => track.stop());
                        }
                    }, 5000);
                }, 1500);

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
                updateStatus('text', 'processing');
                
                // 修改這裡：使用正確的 API 端點和資料格式
                const response = await fetch('/analyze_text', {  // 新的端點
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        text: orderInput.value 
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    currentOrderDetails = result.order_details;
                    currentSpeechText = orderInput.value;  // 使用輸入文字
                    displayOrder(result.order_details, currentSpeechText);
                } else {
                    alert('訂單處理失敗：' + result.message);
                }
                
                orderPrompt.classList.add('hidden');
                
            } catch (error) {
                console.error('處理訂單時發生錯誤:', error);
                alert('處理訂單時發生錯誤，請稍後再試');
            } finally {
                this.disabled = false;
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
        orderItem.innerHTML = `
            <div class="item-name">${item.drink_name}(${item.size}) x${item.quantity}</div>
            <div class="item-options">(${item.sugar}, ${item.ice})</div>
        `;
        container.appendChild(orderItem);
    });
    
    document.getElementById('orderResult').classList.remove('hidden');
}