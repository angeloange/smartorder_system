let mediaRecorder;
let audioChunks = [];
let audioContext;
let analyser;

// 取得麥克風裝置列表
async function getAvailableMicrophones() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter(device => device.kind === 'audioinput');
}

// 開始錄音（在手機版中，我們直接發送請求而不真的錄音）
async function startRecording() {
    try {
        const response = await fetch('/stop_recording', {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            displayOrder(result.order_details, result.speech_text);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// 訂單顯示功能
function displayOrder(orderDetails, speechText) {
    const container = document.getElementById('orderDetails');
    container.innerHTML = '';
    
    // 顯示訂單內容
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

    // 確認按鈕處理
    document.getElementById('confirmOrder').onclick = async () => {
        try {
            const response = await fetch('/confirm_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    order_details: orderDetails,
                    speech_text: speechText
                })
            });
            
            const result = await response.json();
            if (result.status === 'success') {
                // 顯示製作中訊息
                container.innerHTML = '<div class="success-message">好的，尊貴的客人請稍候，正在為您製作飲品</div>';
                document.querySelector('.button-group').classList.add('hidden');
                
                // 5秒後重置頁面
                setTimeout(() => {
                    document.getElementById('orderResult').classList.add('hidden');
                    document.getElementById('startOrder').disabled = false;
                    document.getElementById('orderPrompt').classList.add('hidden');
                    container.innerHTML = '';
                }, 5000);
            }
        } catch (error) {
            console.error('確認訂單時發生錯誤:', error);
        }
    };

    // 取消按鈕處理
    document.getElementById('cancelOrder').onclick = () => {
        document.getElementById('orderResult').classList.add('hidden');
        document.getElementById('startOrder').disabled = false;
        document.getElementById('orderPrompt').classList.add('hidden');
    };
}

// 主要事件監聽器
document.addEventListener('DOMContentLoaded', function() {
    const startOrderBtn = document.getElementById('startOrder');
    
    // 添加觸控事件支援
    document.body.addEventListener('touchstart', function(){}, {passive: true});
    
    startOrderBtn.addEventListener('click', async function() {
        try {
            this.disabled = true;
            document.getElementById('orderPrompt').classList.remove('hidden');
            console.log('開始發送請求...'); // 除錯訊息

            const response = await fetch('/stop_recording', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            console.log('收到回應:', response); // 除錯訊息
            
            const result = await response.json();
            console.log('處理結果:', result); // 除錯訊息
            
            if (result.status === 'success') {
                displayOrder(result.order_details, result.speech_text);
            } else {
                console.error('處理失敗:', result.message);
            }
        } catch (error) {
            console.error('發生錯誤:', error);
            this.disabled = false;
        }
    });
});