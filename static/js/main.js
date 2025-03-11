document.addEventListener('DOMContentLoaded', function() {
    const startOrderBtn = document.getElementById('startOrder');
    
    startOrderBtn.addEventListener('click', async function() {
        try {
            this.disabled = true;
            document.getElementById('orderPrompt').classList.remove('hidden');
            
            const orderText = document.getElementById('orderInput').value;
            
            const response = await fetch('/stop_recording', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: orderText })
            });
            
            const result = await response.json();
            if (result.status === 'success') {
                displayOrder(result.order_details, result.speech_text);
            }
        } catch (error) {
            console.error('Error:', error);
            this.disabled = false;
        }
    });
});

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
                container.innerHTML = '<div class="success-message">好的，尊貴的客人請稍候，正在為您製作飲品</div>';
                document.querySelector('.button-group').classList.add('hidden');
                
                setTimeout(() => {
                    document.getElementById('orderResult').classList.add('hidden');
                    document.getElementById('startOrder').disabled = false;
                    document.getElementById('orderPrompt').classList.add('hidden');
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