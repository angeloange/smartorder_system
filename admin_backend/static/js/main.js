document.addEventListener('DOMContentLoaded', function() {
    // 側邊欄切換
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // 訂單狀態更新
    const statusButtons = document.querySelectorAll('.status-update-btn');
    statusButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const orderId = this.dataset.orderId;
            const newStatus = this.dataset.status;
            
            try {
                const response = await fetch('/api/orders/update_status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        order_id: orderId,
                        status: newStatus
                    })
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    location.reload();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('更新狀態失敗');
            }
        });
    });

    // 數據圖表渲染
    const chartCanvas = document.getElementById('salesChart');
    if (chartCanvas) {
        const ctx = chartCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: '銷售數量',
                    data: chartData.values,
                    backgroundColor: 'rgba(78, 115, 223, 0.5)',
                    borderColor: 'rgba(78, 115, 223, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
});

// 日期範圍選擇器
const dateRangeSelector = document.getElementById('dateRange');
if (dateRangeSelector) {
    dateRangeSelector.addEventListener('change', function() {
        window.location.href = `/analytics?range=${this.value}`;
    });
}
