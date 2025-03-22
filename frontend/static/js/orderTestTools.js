/**
 * 訂單功能整合測試工具
 * 用於協助診斷和修復訂單流程相關問題
 */

class OrderTestTools {
    constructor() {
        console.log('訂單測試工具已初始化');
        
        // 確保orderCore已初始化
        this.ensureOrderCore();
        
        // 延遲初始化事件監控，確保所有依賴都已加載
        setTimeout(() => {
            this.initEventMonitoring();
        }, 1000);
    }
    
    /**
     * 確保orderCore已初始化
     */
    ensureOrderCore() {
        if (!window.orderCore) {
            console.warn('⚠️ orderCore不存在，嘗試恢復...');
            
            // 檢查是否需要加載orderCore-global.js
            if (!window.orderCoreLoaded) {
                console.log('載入orderCore-global.js...');
                const script = document.createElement('script');
                script.src = '/static/js/orderCore-global.js';
                document.head.appendChild(script);
                
                // 稍後再檢查
                setTimeout(() => this.ensureOrderCore(), 1000);
                return;
            }
            
            // 如果全局版本已加載但仍沒有實例，建立臨時版本
            this.createTempOrderCore();
        } else {
            console.log('✅ orderCore已存在');
        }
    }
    
    /**
     * 建立臨時版本的orderCore
     */
    createTempOrderCore() {
        console.log('🔧 創建臨時orderCore');
        
        // 定義一個最小化的orderCore
        window.orderCore = {
            state: 'idle',
            currentOrder: null,
            orderConfirmed: false,
            orderNumber: null,
            waitingTime: 0,
            
            getOrderState() {
                return {
                    state: this.state,
                    hasActiveOrder: !!this.currentOrder,
                    isConfirmed: this.orderConfirmed,
                    orderNumber: this.orderNumber,
                    waitingTime: this.waitingTime
                };
            },
            
            formatOrderText(orderDetails) {
                if (!orderDetails || !Array.isArray(orderDetails)) return "";
                
                return orderDetails.map(item => {
                    const parts = [];
                    if (item.size) parts.push(item.size);
                    if (item.sugar) parts.push(item.sugar);
                    if (item.ice) parts.push(item.ice);
                    parts.push(item.drink_name);
                    
                    return parts.join('');
                }).join('、');
            },
            
            registerCallbacks() {
                // 空方法
            }
        };
        
        console.log('✅ 臨時orderCore已創建');
    }
    
    /**
     * 初始化事件監控
     */
    initEventMonitoring() {
        try {
            // 監聽 fetch 請求
            this.monitorFetch();
            
            // 監聽訂單相關事件
            window.addEventListener('orderPrepared', (event) => {
                console.log('🔍 orderPrepared 事件觸發:', event.detail);
                this.checkOrderState();
            });
            
            // 定期檢查訂單狀態
            setInterval(() => this.checkOrderState(), 5000);
            
            console.log('✅ 事件監控已初始化');
        } catch (error) {
            console.error('❌ 初始化事件監控失敗:', error);
        }
    }
    
    /**
     * 監控 fetch 請求，特別關注訂單相關請求
     */
    monitorFetch() {
        try {
            const originalFetch = window.fetch;
            const self = this;
            
            window.fetch = async function(...args) {
                const url = args[0];
                const options = args[1] || {};
                
                // 檢查是否為訂單相關請求
                const isOrderRequest = 
                    (typeof url === 'string' && (
                        url.includes('/analyze_chat') || 
                        url.includes('/analyze_text') || 
                        url.includes('/confirm_order')
                    ));
                
                if (isOrderRequest) {
                    console.log('🔍 訂單相關請求:', {
                        url,
                        method: options.method || 'GET',
                        body: options.body
                    });
                    
                    try {
                        const response = await originalFetch.apply(this, args);
                        
                        // 複製響應以便檢查
                        const clonedResponse = response.clone();
                        const data = await clonedResponse.json();
                        
                        console.log('🔍 訂單請求響應:', data);
                        
                        // 檢查是否為成功的訂單回應
                        if ((url.includes('/analyze_text') || url.includes('/analyze_chat')) && 
                            data.status === 'success' && data.order_details) {
                            console.log('✅ 成功解析訂單內容');
                            
                            // 嘗試自動設置到orderCore
                            self.trySetOrderData(data.order_details);
                            
                            // 延遲檢查訂單狀態
                            setTimeout(() => self.checkOrderState(), 1000);
                        }
                        
                        return response;
                    } catch (error) {
                        console.error('❌ 訂單請求出錯:', error);
                        throw error;
                    }
                }
                
                return originalFetch.apply(this, args);
            };
            
            console.log('✅ Fetch監控已啟用');
        } catch (error) {
            console.error('❌ 設置Fetch監控失敗:', error);
        }
    }
    
    /**
     * 嘗試設置訂單數據到orderCore
     * @param {Array} orderDetails 訂單詳情
     */
    trySetOrderData(orderDetails) {
        try {
            if (!window.orderCore) {
                this.ensureOrderCore();
            }
            
            if (window.orderCore && Array.isArray(orderDetails) && orderDetails.length > 0) {
                // 設置訂單數據
                window.orderCore.currentOrder = orderDetails;
                window.orderCore.state = 'confirming';
                
                console.log('✅ 訂單數據已設置到orderCore');
                
                // 如果有assistant實例，顯示確認UI
                if (window.assistant && typeof window.assistant.showOrderConfirmation === 'function') {
                    const orderText = window.orderCore.formatOrderText(orderDetails);
                    window.assistant.showOrderConfirmation(orderDetails, orderText);
                    console.log('✅ 訂單確認UI已顯示');
                }
            }
        } catch (error) {
            console.error('❌ 設置訂單數據失敗:', error);
        }
    }
    
    /**
     * 檢查訂單狀態
     * @param {number} delay 可選的延遲毫秒數
     */
    checkOrderState(delay = 0) {
        const check = () => {
            try {
                if (!window.orderCore) {
                    console.error('❌ orderCore 不存在');
                    this.ensureOrderCore();
                    return;
                }
                
                const state = window.orderCore.getOrderState();
                console.log('🔍 當前訂單狀態:', state);
                
                // 如果有訂單但狀態不正確
                if (state.hasActiveOrder && state.state !== 'confirming') {
                    console.warn('⚠️ 訂單狀態異常:', state);
                    this.attemptFix();
                }
                
                // 如果orderCore有訂單但沒有顯示確認UI
                if (state.hasActiveOrder && state.state === 'confirming') {
                    this.checkConfirmationUI();
                }
            } catch (error) {
                console.error('❌ 檢查訂單狀態時發生錯誤:', error);
            }
        };
        
        if (delay > 0) {
            setTimeout(check, delay);
        } else {
            check();
        }
    }
    
    /**
     * 檢查確認UI是否顯示
     */
    checkConfirmationUI() {
        try {
            const chatMessages = document.getElementById('chatMessages');
            if (!chatMessages) return;
            
            const confirmationExists = Array.from(chatMessages.querySelectorAll('.message.assistant')).some(
                msg => msg.textContent.includes('確認一下訂單') && msg.textContent.includes('請問確認')
            );
            
            if (!confirmationExists && window.orderCore && window.orderCore.currentOrder) {
                console.warn('⚠️ 訂單確認UI未顯示，嘗試修復');
                this.showConfirmationUI();
            }
        } catch (error) {
            console.error('❌ 檢查確認UI時發生錯誤:', error);
        }
    }
    
    /**
     * 嘗試顯示確認UI
     */
    showConfirmationUI() {
        try {
            if (!window.orderCore || !window.orderCore.currentOrder) return;
            
            const orderText = window.orderCore.formatOrderText(window.orderCore.currentOrder);
            
            // 嘗試通過不同方式添加確認訊息
            if (window.assistant && typeof window.assistant.addMessage === 'function') {
                window.assistant.addMessage('assistant', 
                    `我幫您確認一下訂單：${orderText}\n\n請問確認訂購嗎？`);
                console.log('✅ 已通過 assistant.addMessage 添加訂單確認UI');
                return;
            }
            
            // 如果assistant不可用，直接操作DOM
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                // 創建消息元素
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message assistant order-confirmation';
                
                // 添加消息內容
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = `我幫您確認一下訂單：${orderText}\n\n請問確認訂購嗎？`;
                messageDiv.appendChild(contentDiv);
                
                // 添加確認和取消按鈕
                const buttonsDiv = document.createElement('div');
                buttonsDiv.className = 'confirm-buttons';
                
                // 確認按鈕
                const confirmBtn = document.createElement('button');
                confirmBtn.className = 'confirm-btn';
                confirmBtn.textContent = '確認訂單';
                confirmBtn.addEventListener('click', () => {
                    if (window.orderCore && typeof window.orderCore.confirmOrder === 'function') {
                        window.orderCore.confirmOrder();
                    }
                });
                
                // 取消按鈕
                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'cancel-btn';
                cancelBtn.textContent = '取消訂單';
                cancelBtn.addEventListener('click', () => {
                    if (window.orderCore && typeof window.orderCore.cancelOrder === 'function') {
                        const message = window.orderCore.cancelOrder();
                        // 添加系統消息
                        const systemMsg = document.createElement('div');
                        systemMsg.className = 'message assistant';
                        systemMsg.textContent = message;
                        chatMessages.appendChild(systemMsg);
                    }
                });
                
                buttonsDiv.appendChild(confirmBtn);
                buttonsDiv.appendChild(cancelBtn);
                messageDiv.appendChild(buttonsDiv);
                
                // 添加到聊天容器
                chatMessages.appendChild(messageDiv);
                
                // 滾動到底部
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                console.log('✅ 已通過 DOM 操作添加訂單確認UI');
            } else {
                console.error('❌ 無法找到聊天消息容器');
            }
        } catch (error) {
            console.error('❌ 顯示確認UI時發生錯誤:', error);
        }
    }
    
    /**
     * 嘗試修復訂單流程
     */
    attemptFix() {
        try {
            console.log('🔧 嘗試修復訂單流程');
            
            if (!window.orderCore) {
                this.ensureOrderCore();
                return;
            }
            
            if (window.orderCore.currentOrder) {
                // 設置正確的狀態
                window.orderCore.state = 'confirming';
                
                // 確保有確認UI
                this.showConfirmationUI();
                
                console.log('✅ 修復完成');
            } else {
                console.warn('⚠️ 無法修復，缺少訂單數據');
            }
        } catch (error) {
            console.error('❌ 修復時發生錯誤:', error);
        }
    }
    
    /**
     * 模擬訂單輸入測試
     * @param {string} text 測試訂單文本
     */
    async testOrderInput(text) {
        try {
            console.log('🧪 測試訂單輸入:', text);
            
            // 直接分析訂單
            const response = await fetch('/analyze_text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            
            const result = await response.json();
            console.log('🧪 訂單分析結果:', result);
            
            if (result.status === 'success' && result.order_details) {
                console.log('✅ 訂單分析成功');
                
                // 嘗試設置到orderCore
                this.trySetOrderData(result.order_details);
                
                // 用戶提示
                if (typeof Swal === 'function') {
                    Swal.fire({
                        title: '訂單分析成功',
                        html: `
                            <div style="text-align:left;margin-bottom:10px;">
                                <strong>訂單詳情:</strong>
                                <pre style="background:#f8f9fa;padding:10px;border-radius:5px;text-align:left;overflow:auto;max-height:200px;">
${JSON.stringify(result.order_details, null, 2)}
                                </pre>
                            </div>
                        `,
                        icon: 'success'
                    });
                } else {
                    alert('訂單分析成功：' + JSON.stringify(result.order_details, null, 2));
                }
            } else {
                console.error('❌ 訂單分析失敗:', result.message || '未知錯誤');
                
                if (typeof Swal === 'function') {
                    Swal.fire({
                        title: '訂單分析失敗',
                        text: result.message || '未知錯誤',
                        icon: 'error'
                    });
                } else {
                    alert('訂單分析失敗：' + (result.message || '未知錯誤'));
                }
            }
        } catch (error) {
            console.error('❌ 測試時發生錯誤:', error);
            
            if (typeof Swal === 'function') {
                Swal.fire({
                    title: '測試時發生錯誤',
                    text: error.message,
                    icon: 'error'
                });
            } else {
                alert('測試時發生錯誤：' + error.message);
            }
        }
    }
}

// 等待頁面加載完成再初始化工具
document.addEventListener('DOMContentLoaded', function() {
    console.log('頁面加載完成，初始化訂單測試工具');
    
    // 延遲初始化，確保其他腳本已加載
    setTimeout(() => {
        // 創建全局測試工具實例
        window.orderTestTools = new OrderTestTools();
        console.log('訂單測試工具已加載');
    }, 1000);
});

// 立即創建一個簡單版本，確保能處理早期事件
window.orderTestTools = {
    testOrderInput: function(text) {
        console.log('簡易版testOrderInput:', text);
        alert('測試工具正在初始化中，請稍後再試');
    },
    checkOrderState: function() {
        console.log('簡易版checkOrderState');
    },
    attemptFix: function() {
        console.log('簡易版attemptFix');
    }
};

// 若在模塊環境中，導出類
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrderTestTools;
}
