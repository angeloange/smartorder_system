/**
 * 訂單處理核心 - 處理點餐流程和訂單管理
 */
class OrderCore {
    constructor() {
        // 初始化訂單狀態
        this.currentOrder = null;
        this.orderConfirmed = false;
        this.orderNumber = null;
        this.state = 'idle'; // idle, analyzing, confirming, processing, completed
        this.waitingTime = 0; // 等候時間(分鐘)
        
        // 初始化回調函數
        this.callbacks = {
            onOrderProcessStart: null,
            onOrderProcessSuccess: null,
            onOrderProcessFail: null,
            onOrderConfirm: null,
            onOrderCancel: null,
            onOrderStatusUpdate: null
        };
        
        // 飲料數據
        this.drinks = [
            '珍珠奶茶', '紅茶', '綠茶', '奶茶', '青茶', '烏龍茶', '鮮奶茶',
            '冬瓜茶', '檸檬茶', '蜂蜜檸檬', '梅子綠茶', '冬瓜檸檬', '普洱茶',
            '奶綠', '烏龍奶茶', '焦糖奶茶', '波霸奶茶', '椰果奶茶', '蜂蜜奶茶',
            '仙草奶茶', '布丁奶茶', '巧克力牛奶', '美式咖啡', '卡布奇諾', 
            '拿鐵咖啡', '摩卡咖啡', '烏龍拿鐵', '紅茶咖啡', '牛奶咖啡'
        ];
        
        // 初始化 Socket.IO
        this.initSocketIO();
        
        // 初始化訂單事件監聽器
        this.initEventListeners();
    }
    
    /**
     * 註冊回調函數
     * @param {Object} callbacks 回調函數集合
     */
    registerCallbacks(callbacks) {
        this.callbacks = {...this.callbacks, ...callbacks};
    }
    
    /**
     * 處理用戶輸入，判斷是否為點餐意圖
     * @param {string} text 用戶輸入
     * @return {boolean} 是否為點餐意圖
     */
    isOrderIntent(text) {
        // 檢查是否包含飲料名稱
        const hasDrink = this.drinks.some(drink => text.includes(drink));
        
        // 如果只是飲料名稱，無需其他判斷
        if (this.drinks.some(drink => text === drink)) {
            return true;
        }
        
        // 檢查是否包含甜度或冰塊關鍵詞
        const sugarKeywords = ['全糖', '七分糖', '半糖', '三分糖', '微糖', '無糖'];
        const iceKeywords = ['正常冰', '少冰', '微冰', '去冰', '熱', '溫', '常溫'];
        
        const hasSugarOption = sugarKeywords.some(option => text.includes(option));
        const hasIceOption = iceKeywords.some(option => text.includes(option));
        
        // 檢查是否包含訂購關鍵詞
        const orderKeywords = ['要', '買', '點', '杯', '來一杯', '訂', '喝', '一杯', '兩杯'];
        const hasOrderKeyword = orderKeywords.some(keyword => text.includes(keyword));
        
        // 如果僅是飲料名稱而沒有其他內容，也算是點餐意圖
        if (hasDrink && text.length < 15 && !text.includes('?') && !text.includes('？')) {
            return true;
        }
        
        // 一般情況下判斷是否為點餐意圖
        return hasDrink && (hasOrderKeyword || hasSugarOption || hasIceOption);
    }
    
    /**
     * 分析訂單內容
     * @param {string} text 用戶輸入
     * @return {Promise} 訂單分析結果
     */
    async analyzeOrder(text) {
        try {
            // 通知開始處理
            if (this.callbacks.onOrderProcessStart) {
                this.callbacks.onOrderProcessStart();
            }
            
            this.state = 'analyzing';
            console.log('分析訂單內容:', text);
            
            // 如果只包含飲料名稱，自動添加"一杯"前綴
            const isDrinkOnly = this.drinks.some(drink => text.trim() === drink);
            if (isDrinkOnly) {
                text = `一杯${text}`;
                console.log('修正純飲料名稱輸入:', text);
            }
            
            // 發送到後端分析
            const response = await fetch('/analyze_text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            
            const result = await response.json();
            console.log('訂單分析結果:', result);
            
            // 如果分析成功，保存訂單信息
            if (result.status === 'success' && result.order_details && result.order_details.length > 0) {
                this.currentOrder = result.order_details;
                this.state = 'confirming';
                
                // 格式化訂單文本
                const orderText = this.formatOrderText(result.order_details);
                
                // 回調通知
                if (this.callbacks.onOrderProcessSuccess) {
                    this.callbacks.onOrderProcessSuccess({
                        orderDetails: result.order_details,
                        orderText: orderText,
                        message: `我幫您確認一下訂單：${orderText}\n\n請問確認訂購嗎？` 
                    });
                }
                
                return {
                    success: true,
                    orderDetails: result.order_details,
                    orderText: orderText
                };
            } else {
                // 分析失敗
                this.state = 'idle';
                
                if (this.callbacks.onOrderProcessFail) {
                    this.callbacks.onOrderProcessFail({
                        message: result.message || '無法識別訂單內容'
                    });
                }
                
                return {
                    success: false,
                    message: result.message || '訂單分析失敗'
                };
            }
        } catch (error) {
            console.error('訂單分析錯誤:', error);
            this.state = 'idle';
            
            if (this.callbacks.onOrderProcessFail) {
                this.callbacks.onOrderProcessFail({
                    message: '訂單處理出錯'
                });
            }
            
            return {
                success: false,
                message: '訂單處理出錯'
            };
        }
    }
    
    /**
     * 確認訂單
     * @return {Promise} 訂單確認結果
     */
    async confirmOrder() {
        try {
            // ...現有代碼...
            
            const response = await fetch('/confirm_order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_details: this.currentOrder })
            });
            
            const result = await response.json();
            console.log('後端訂單確認結果:', result);
            
            if (result.status === 'success') {
                // 保存訂單編號
                this.orderNumber = result.order_number;
                this.state = 'confirmed';
                
                return {
                    success: true,
                    message: result.message || `訂單已確認！您的取餐號碼是 ${this.orderNumber}，謝謝您的光臨。`,
                    orderNumber: this.orderNumber,
                    waitingTime: '3分鐘'
                };
            } else {
                return {
                    success: false,
                    message: result.message || '訂單確認失敗，請稍後再試。'
                };
            }
        } catch (error) {
            console.error('確認訂單時出錯:', error);
            return {
                success: false,
                message: '處理訂單請求時出現錯誤，請稍後再試。'
            };
        }
    }
    /**
     * 取消訂單
     * @return {string} 取消訊息
     */
    cancelOrder() {
        // 重設所有訂單相關狀態
        this.currentOrder = null;
        this.orderConfirmed = false;
        this.state = 'idle';
        
        // 清除相關 UI
        const orderResult = document.getElementById('orderResult');
        if (orderResult) {
            orderResult.classList.add('hidden');
        }
        
        // 通知回調
        if (this.callbacks.onOrderCancel) {
            this.callbacks.onOrderCancel();
        }
        
        // 返回取消訊息
        return '訂單已取消，請問還需要其他飲料嗎？';
    }
    
    /**
     * 格式化訂單文字
     * @param {Array} orderDetails 訂單詳情
     * @return {string} 格式化的訂單文字
     */
    formatOrderText(orderDetails) {
        return orderDetails.map(item => {
            const parts = [];
            if (item.size) parts.push(item.size);
            if (item.sugar) parts.push(item.sugar);
            if (item.ice) parts.push(item.ice);
            parts.push(item.drink_name);
            
            let orderText = parts.join('');
            if (item.quantity > 1) {
                orderText += ` ${item.quantity}杯`;
            }
            return orderText;
        }).join('、');
    }
    
    /**
     * 只更新等待時間顯示
     */
    updateWaitingTimeDisplay() {
        try {
            // 只更新等待時間顯示
            const waitingTimeDisplay = document.querySelector('.waiting-time');
            if (waitingTimeDisplay) {
                waitingTimeDisplay.textContent = `${this.waitingTime} 分鐘`;
                waitingTimeDisplay.classList.add('flash');
                setTimeout(() => waitingTimeDisplay.classList.remove('flash'), 2000);
            }
        } catch (error) {
            console.error('更新等待時間顯示錯誤:', error);
        }
    }

    /**
     * 更新訂單顯示
     * 這個方法現在只在收到Socket.io通知時調用
     */
    updateOrderDisplay() {
        try {
            if (!this.orderNumber) return;
            
            // 更新訂單號顯示
            const numberDisplay = document.querySelector('.number-display');
            if (numberDisplay) {
                numberDisplay.textContent = this.orderNumber;
                numberDisplay.classList.add('flash');
                // 播放提示音效
                this.playNotificationSound();
                // 顯示提示文字
                const infoText = numberDisplay.nextElementSibling;
                if (infoText && infoText.classList.contains('info-text')) {
                    infoText.textContent = '您的飲料已完成，請取餐！';
                    infoText.classList.add('highlight');
                    setTimeout(() => infoText.classList.remove('highlight'), 5000);
                }
                setTimeout(() => numberDisplay.classList.remove('flash'), 2000);
            }
        } catch (error) {
            console.error('更新訂單顯示錯誤:', error);
        }
    }

    /**
     * 播放通知音效
     */
    playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.play();
        } catch (error) {
            console.error('播放通知音效出錯:', error);
        }
    }

    /**
     * 獲取當前訂單狀態
     * @return {Object} 訂單狀態
     */
    getOrderState() {
        return {
            state: this.state,
            hasActiveOrder: !!this.currentOrder,
            isConfirmed: this.orderConfirmed,
            orderNumber: this.orderNumber,
            waitingTime: this.waitingTime
        };
    }
    
    /**
     * 處理訂單狀態更新
     * @param {Object} data 狀態數據
     */
    handleOrderStatusUpdate(data) {
        if (!data || !data.order_number) return;
        
        // 檢查是否是當前訂單
        const isCurrentOrder = 
            this.orderNumber === data.order_number ||
            this.fullOrderNumber === data.order_number ||
            (this.orderNumber && data.order_number.includes(this.orderNumber)) ||
            (this.fullOrderNumber && data.order_number.includes(this.fullOrderNumber));
            
        if (!isCurrentOrder) return;
        
        console.log('訂單狀態更新:', data);
        
        // 更新等待時間
        if (data.status === 'preparing') {
            this.waitingTime = Math.max(1, this.waitingTime - 2);
            this.updateWaitingTimeDisplay();
        } else if (data.status === 'ready' || data.status === 'completed') {
            this.waitingTime = 0;
            // 訂單完成/就緒時，更新取餐號碼顯示
            this.updateOrderDisplay();
        }
        
        // 回調通知
        if (this.callbacks.onOrderStatusUpdate) {
            this.callbacks.onOrderStatusUpdate({
                status: data.status,
                orderNumber: this.orderNumber,
                waitingTime: this.waitingTime,
                message: this.getStatusMessage(data.status)
            });
        }
    }
    
    /**
     * 獲取狀態消息
     * @param {string} status 狀態
     * @return {string} 狀態消息
     */
    getStatusMessage(status) {
        switch(status) {
            case 'pending':
                return `您的訂單 ${this.orderNumber} 已進入處理佇列，請稍候。`;
            case 'preparing':
                return `您的訂單 ${this.orderNumber} 正在製作中，預計等候時間約 ${this.waitingTime} 分鐘。`;
            case 'ready':
                return `您的訂單 ${this.orderNumber} 已完成，請前往櫃檯取餐。`;
            case 'completed':
                return `您的訂單 ${this.orderNumber} 已完成，感謝您的光臨。`;
            default:
                return `您的訂單 ${this.orderNumber} 狀態已更新為: ${status}`;
        }
    }
    
    /**
     * 初始化 Socket.IO 連接
     */
    initSocketIO() {
        try {
            if (typeof io !== 'function') {
                console.error('Socket.IO 未加載，無法初始化連接');
                return;
            }
            
            this.socket = io();
            
            // 監聽訂單狀態更新
            this.socket.on('order_status_update', (data) => {
                this.handleOrderStatusUpdate(data);
            });
            
            // 監聽訂單完成事件
            this.socket.on('order_completed', (data) => {
                if (data.order_number === this.orderNumber || 
                    data.order_number === this.fullOrderNumber) {
                    this.handleOrderStatusUpdate({
                        order_number: data.order_number,
                        status: 'completed'
                    });
                }
            });
        } catch (error) {
            console.error('初始化 Socket.IO 時發生錯誤:', error);
        }
    }
    
    /**
     * 監聽全局訂單事件
     */
    initEventListeners() {
        // 監聽訂單準備完成事件
        window.addEventListener('orderPrepared', (event) => {
            console.log('收到訂單準備完成事件:', event.detail);
            
            // 設置訂單狀態為確認中
            this.currentOrder = event.detail.orderDetails;
            this.state = 'confirming';
            
            // 如果有必要，添加訂單確認UI
            this.ensureOrderConfirmationUI();
        });
        
        // 監聽其他訂單相關事件
        // ...existing code...
    }

    /**
     * 確保訂單確認UI顯示
     */
    ensureOrderConfirmationUI() {
        if (!this.currentOrder || this.state !== 'confirming') return;
        
        // 檢查是否已經顯示了訂單確認訊息
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const confirmationExists = Array.from(chatMessages.querySelectorAll('.message.assistant')).some(
            msg => msg.textContent.includes('確認一下訂單') && msg.textContent.includes('請問確認')
        );
        
        if (!confirmationExists) {
            console.log('訂單確認UI未顯示，手動添加');
            const orderText = this.formatOrderText(this.currentOrder);
            
            // 如果有全局助手可用
            if (window.assistant && typeof window.assistant.addMessage === 'function') {
                window.assistant.addMessage('assistant', 
                    `我幫您確認一下訂單：${orderText}\n\n請問確認訂購嗎？`);
            }
        }
    }

    /**
     * 從API分析結果設置訂單
     * @param {Object} result 分析結果
     */
    setOrderFromAnalysisResult(result) {
        if (!result || !result.is_order) return false;
        
        if (result.order_details && Array.isArray(result.order_details) && result.order_details.length > 0) {
            console.log('從分析結果設置訂單:', result.order_details);
            this.currentOrder = result.order_details;
            this.state = 'confirming';
            
            // 確保訂單確認UI顯示
            this.ensureOrderConfirmationUI();
            return true;
        }
        
        return false;
    }
}

// 創建全局實例並立即導出
const orderCore = new OrderCore();
window.orderCore = orderCore; // 確保在全局作用域可訪問