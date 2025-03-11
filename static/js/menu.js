const menuData = {
    tea: [
        { name: "青茶", price: "45", description: "清香回甘" },
        { name: "烏龍茶", price: "45", description: "醇厚甘醇" },
        { name: "紅茶", price: "40", description: "濃郁香醇" },
        { name: "綠茶", price: "40", description: "清爽回甘" },
        { name: "檸檬茶", price: "50", description: "清新酸甜" },
        { name: "蜂蜜檸檬", price: "55", description: "天然蜂蜜" }
    ],
    milkTea: [
        { name: "波霸奶茶", price: "55", description: "香醇滑順" },
        { name: "珍珠奶茶", price: "55", description: "口感紮實" },
        { name: "椰果奶茶", price: "55", description: "清爽脆嫩" },
        { name: "布丁奶茶", price: "60", description: "滑嫩香甜" },
        { name: "仙草奶茶", price: "60", description: "傳統風味" },
        { name: "焦糖奶茶", price: "60", description: "濃郁香甜" }
    ],
    coffee: [
        { name: "美式咖啡", price: "50", description: "醇厚濃郁" },
        { name: "拿鐵咖啡", price: "60", description: "絲綢口感" },
        { name: "卡布奇諾", price: "60", description: "綿密奶泡" },
        { name: "焦糖瑪奇朵", price: "65", description: "層次豐富" },
        { name: "摩卡咖啡", price: "65", description: "可可香醇" },
        { name: "香草拿鐵", price: "65", description: "清香怡人" }
    ]
};

function createMenuItem(item) {
    return `
        <div class="menu-item">
            <div class="menu-item-name">${item.name}</div>
            <div class="menu-item-price">NT$ ${item.price}</div>
            <div class="menu-item-description">${item.description}</div>
        </div>
    `;
}

function loadMenu() {
    // 載入菜單項目
    Object.keys(menuData).forEach(category => {
        const container = document.querySelector(`#${category}`);
        if (container) {
            container.innerHTML = menuData[category]
                .map(item => createMenuItem(item))
                .join('');
        }
    });

    // 載入熱銷排行
    const hotSales = ["波霸奶茶", "美式咖啡", "檸檬茶"];
    const hotSalesContainer = document.querySelector('.hot-sales');
    hotSales.forEach((item, index) => {
        const li = document.createElement('li');
        li.textContent = `${index + 1}. ${item}`;
        hotSalesContainer.appendChild(li);
    });

    // 載入天氣推薦
    const currentTemp = Math.floor(Math.random() * (35 - 15 + 1)) + 15;
    const recommendations = getWeatherRecommendations(currentTemp);
    const weatherContainer = document.querySelector('.weather-recommend');
    recommendations.forEach((item, index) => {
        const li = document.createElement('li');
        li.textContent = `${index + 1}. ${item}`;
        weatherContainer.appendChild(li);
    });
}

function getWeatherRecommendations(temp) {
    if (temp >= 30) {
        return ["冰綠茶", "檸檬冰茶", "美式冰咖啡"];
    } else if (temp <= 20) {
        return ["熱奶茶", "熱拿鐵", "薑母茶"];
    } else {
        return ["烏龍茶", "珍珠奶茶", "卡布奇諾"];
    }
}

// 更新取餐資訊
function updateOrderInfo() {
    const currentNumber = document.getElementById('currentNumber');
    const waitingCount = document.getElementById('waitingCount');
    const waitingTime = document.getElementById('waitingTime');
    
    setInterval(() => {
        const number = Math.floor(Math.random() * 20) + 1;
        const count = Math.floor(Math.random() * 10);
        currentNumber.textContent = `A${number}`;
        waitingCount.textContent = count;
        waitingTime.textContent = `預計等待 ${count * 2} 分鐘`;
    }, 5000);
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadMenu();
    updateOrderInfo();
});