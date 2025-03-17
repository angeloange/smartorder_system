document.addEventListener('DOMContentLoaded', function() {
    // 側邊欄收合功能
    let sidebar = document.querySelector(".sidebar");
    let sidebarBtn = document.querySelector(".bx-menu");
    
    sidebarBtn.addEventListener("click", () => {
        sidebar.classList.toggle("close");
    });

    // 訂單狀態更新功能
    const statusButtons = document.querySelectorAll('.status-update-btn');
    statusButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const orderId = button.dataset.orderId;
            const newStatus = button.dataset.status;
            
            try {
                const response = await fetch(`/api/orders/${orderId}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ status: newStatus })
                });
                
                if (response.ok) {
                    location.reload();
                } else {
                    alert('更新失敗，請稍後再試');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('系統錯誤，請稍後再試');
            }
        });
    });
});