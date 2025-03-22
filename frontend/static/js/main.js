/**
 * 主程序入口 - 初始化應用
 */
import AssistantCore from './assistantCore.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 載入完成，初始化應用...');
    
    // 檢測是否為移動設備
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // 移動設備需要解鎖音頻
    if (isMobile) {
        showAudioUnlockButton();
    } else {
        // 桌面設備直接初始化
        initApp();
    }
    
    // 初始化 Socket.IO 連接
    initSocketIO();
    
    // 加載熱銷排行
    loadTopDrinks();
});

/**
 * 顯示音頻解鎖按鈕（移動設備需要）
 */
function showAudioUnlockButton() {
    const unlockDiv = document.createElement('div');
    unlockDiv.className = 'audio-unlock-container';
    unlockDiv.innerHTML = `
        <button class="unlock-button">
            <i class="fas fa-volume-up"></i> 點擊啟用語音功能
        </button>
    `;
    document.body.appendChild(unlockDiv);
    
    // 添加樣式
    const style = document.createElement('style');
    style.textContent = `
        .audio-unlock-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .unlock-button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 30px;
            font-size: 18px;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s;
        }
        .unlock-button:hover {
            background: #388E3C;
            transform: scale(1.05);
        }
    `;
    document.head.appendChild(style);
    
    // 點擊解鎖
    unlockDiv.querySelector('.unlock-button').addEventListener('click', () => {
        unlockAudio(() => {
            unlockDiv.remove();
            initApp();
        });
    });
}

/**
 * 解鎖音頻（用於移動設備）
 * @param {Function} callback 成功後的回調
 */
function unlockAudio(callback) {
    try {
        // 播放無聲音頻
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const buffer = audioContext.createBuffer(1, 1, 22050);
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.start(0);
        
        // 使用 Web Speech API 解鎖
        if (window.speechSynthesis) {
            const utterance = new SpeechSynthesisUtterance('');
            utterance.volume = 0;
            window.speechSynthesis.speak(utterance);
        }
        
        // 執行回調
        if (callback) {
            setTimeout(callback, 100);
        }
    } catch (e) {
        console.error('解鎖音頻失敗:', e);
        if (callback) {
            callback();
        }
    }
}

/**
 * 初始化應用
 */
function initApp() {
    // 初始化虛擬助手
    window.assistant = new AssistantCore();
    
    // 其他初始化邏輯
    // ...
    
    console.log('應用初始化完成');
}

/**
 * 初始化 Socket.IO 連接
 */
function initSocketIO() {
    try {
        if (typeof io !== 'function') {
            console.error('Socket.IO 未加載');
            return;
        }
        
        const socket = io();
        
        socket.on('connect', () => {
            console.log('Socket.IO 已連接');
        });
        
        socket.on('connect_error', (error) => {
            console.error('Socket.IO 連接錯誤:', error);
        });
        
        // 全局 socket 對象
        window.socket = socket;
    } catch (error) {
        console.error('初始化 Socket.IO 失敗:', error);
    }
}

/**
 * 載入熱銷排行
 */
async function loadTopDrinks() {
    try {
        const response = await fetch('/monthly_top_drinks');
        const result = await response.json();
        
        const container = document.querySelector('.rank-list.hot-sales');
        if (container && result.data && result.data.length > 0) {
            container.innerHTML = '';
            result.data.forEach((item, index) => {
                const div = document.createElement('div');
                div.className = 'rank-item';
                div.textContent = `${index + 1}. ${item.name} (${item.count}杯)`;
                container.appendChild(div);
            });
        } else if (container) {
            container.innerHTML = '<div class="rank-item">暫無熱銷數據</div>';
        }
    } catch (error) {
        console.error('載入熱銷排行失敗:', error);
        const container = document.querySelector('.rank-list.hot-sales');
        if (container) {
            container.innerHTML = '<div class="rank-item">載入失敗</div>';
        }
    }
}
