from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Admin, Order, OrderStatus
from config import Config
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
app.config.from_object(Config)

# 初始化資料庫
db.init_app(app)

# 初始化登入管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Admin.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        flash('帳號或密碼錯誤')
    return render_template('login.html')

# 儀表板
@app.route('/')
@login_required
def dashboard():
    # 獲取今日訂單統計
    today = datetime.utcnow().date()
    stats = {
        'total_orders': Order.query.filter(Order.order_date == today).count(),
        'pending_orders': Order.query.filter_by(status=OrderStatus.PENDING).count(),
        'processing_orders': Order.query.filter_by(status=OrderStatus.PROCESSING).count(),
        'completed_orders': Order.query.filter_by(status=OrderStatus.COMPLETED).count()
    }
    return render_template('dashboard.html', stats=stats)

# 訂單管理
@app.route('/orders')
@login_required
def orders():
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Order.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('orders.html', orders=orders, current_status=status)

# API：更新訂單狀態
@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status in [status.value for status in OrderStatus]:
        order.status = new_status
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': '無效的狀態'}), 400

# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)