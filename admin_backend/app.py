from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from .models import db, Admin, Order, OrderStatus  # 修改為相對導入
from config import Config
from datetime import datetime, timedelta
import pandas as pd
from werkzeug.utils import secure_filename
import os
import json

app = Flask(__name__)
app.config.from_object(Config)

# 在 Config 類中添加上傳檔案配置
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 確保上傳目錄存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化資料庫
db.init_app(app)

# 初始化登入管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 確保這行存在
login_manager.login_message = '請先登入'  # 添加中文提示訊息

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
    print("開始載入儀表板...")
    try:
        # 獲取今日訂單統計
        today = datetime.utcnow().date()
        print(f"正在查詢今日({today})訂單...")
        
        stats = {
            'total_orders': Order.query.filter(Order.order_date == today).count(),
            'pending_orders': Order.query.filter_by(status=OrderStatus.PENDING).count(),
            'processing_orders': Order.query.filter_by(status=OrderStatus.PROCESSING).count(),
            'completed_orders': Order.query.filter_by(status=OrderStatus.COMPLETED).count()
        }
        print("訂單統計查詢完成:", stats)
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        print(f"儀表板載入錯誤: {str(e)}")
        return f"載入錯誤: {str(e)}", 500
# 訂單管理
@app.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = Order.query
    if status != 'all':
        query = query.filter(Order.status == OrderStatus[status.upper()])
    
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('orders.html', 
                         orders=orders, 
                         current_status=status,
                         OrderStatus=OrderStatus)  # 傳遞 OrderStatus 到模板

# 產品管理路由
@app.route('/products')
@login_required
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

# 產品 API 端點
@app.route('/api/products', methods=['GET', 'POST'])
@login_required
def api_products():
    if request.method == 'GET':
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products])
    
    elif request.method == 'POST':
        try:
            data = request.form
            product = Product(
                name=data['name'],
                price=float(data['price']),
                description=data.get('description', ''),
                is_available=True
            )
            
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    product.image_url = f'/static/uploads/{filename}'
            
            db.session.add(product)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '產品已新增'})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/products/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'GET':
        return jsonify(product.to_dict())
        
    elif request.method == 'PUT':
        try:
            data = request.form
            product.name = data.get('name', product.name)
            product.price = float(data.get('price', product.price))
            product.description = data.get('description', product.description)
            
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    # 刪除舊圖片
                    if product.image_url:
                        old_file = os.path.join(app.root_path, product.image_url.lstrip('/'))
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    product.image_url = f'/static/uploads/{filename}'
            
            db.session.commit()
            return jsonify({'status': 'success', 'message': '產品已更新'})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
            
    elif request.method == 'DELETE':
        try:
            # 刪除產品圖片
            if product.image_url:
                file_path = os.path.join(app.root_path, product.image_url.lstrip('/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            db.session.delete(product)
            db.session.commit()
            return jsonify({'status': 'success', 'message': '產品已刪除'})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/products/<int:product_id>/status', methods=['PUT'])
@login_required
def update_product_status(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    try:
        product.is_available = data['is_available']
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

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

# 數據分析頁面
@app.route('/analytics')
@login_required
def analytics():
    range_type = request.args.get('range', 'today')
    
    # 計算日期範圍
    today = datetime.now().date()
    if range_type == 'week':
        start_date = today - timedelta(days=7)
    elif range_type == 'month':
        start_date = today.replace(day=1)
    elif range_type == 'year':
        start_date = today.replace(month=1, day=1)
    else:  # today
        start_date = today
    
    # 獲取統計數據
    stats = {
        'total_orders': Order.query.filter(Order.order_date >= start_date).count(),
        'total_revenue': db.session.query(db.func.sum(Order.total_amount))
            .filter(Order.order_date >= start_date)
            .scalar() or 0,
    }
    
    # 計算增長率（與前一個時期比較）
    previous_start = start_date - (today - start_date)
    previous_orders = Order.query.filter(
        Order.order_date >= previous_start,
        Order.order_date < start_date
    ).count()
    
    previous_revenue = db.session.query(db.func.sum(Order.total_amount))\
        .filter(Order.order_date >= previous_start,
                Order.order_date < start_date)\
        .scalar() or 0
    
    stats['order_growth'] = calculate_growth(stats['total_orders'], previous_orders)
    stats['revenue_growth'] = calculate_growth(stats['total_revenue'], previous_revenue)
    
    # 獲取銷售趨勢數據
    trend_data = get_sales_trend(start_date)
    
    # 獲取熱門商品數據
    top_products = get_top_products(start_date)
    
    return render_template('analytics.html',
                         stats=stats,
                         chart_data=trend_data,
                         top_products=top_products,
                         range=range_type)

def calculate_growth(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    return round(((current - previous) / previous) * 100, 2)

def get_sales_trend(start_date):
    # 獲取每日銷售數據
    daily_sales = db.session.query(
        Order.order_date,
        db.func.count(Order.id).label('orders'),
        db.func.sum(Order.total_amount).label('revenue')
    ).filter(
        Order.order_date >= start_date
    ).group_by(
        Order.order_date
    ).all()
    
    dates = []
    sales = []
    for date, orders, revenue in daily_sales:
        dates.append(date.strftime('%Y-%m-%d'))
        sales.append(float(revenue or 0))
    
    return {
        'labels': dates,
        'sales': sales
    }

def get_top_products(start_date):
    # 獲取熱門商品數據
    top_products = db.session.query(
        Order.drink_name,
        db.func.count(Order.id).label('count')
    ).filter(
        Order.order_date >= start_date
    ).group_by(
        Order.drink_name
    ).order_by(
        db.text('count DESC')
    ).limit(5).all()
    
    return {
        'labels': [p[0] for p in top_products],
        'data': [p[1] for p in top_products]
    }

# 系統設定頁面
@app.route('/settings')
@login_required
def settings():
    # 獲取系統設定
    system_settings = {
        'opening_time': '09:00',
        'closing_time': '21:00',
        'closed_days': [],  # 0=週一, 6=週日
    }
    
    # 取得最後備份時間
    last_backup = None  # 這裡可以從資料庫或檔案系統獲取最後備份時間
    
    return render_template('settings.html', 
                         settings=system_settings,
                         last_backup_time=last_backup)

# 更新個人資料
@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        user = current_user
        
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': '個人資料已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# 修改密碼
@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_user.check_password(current_password):
            return jsonify({'status': 'error', 'message': '目前密碼錯誤'}), 400
            
        current_user.set_password(new_password)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '密碼已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# 更新系統設定
@app.route('/api/settings', methods=['PUT'])
@login_required
def update_settings():
    try:
        data = request.get_json()
        
        # 這裡可以將設定儲存到資料庫或設定檔
        # 例如：更新營業時間、休息日等
        
        return jsonify({'status': 'success', 'message': '設定已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# 資料備份
@app.route('/api/backup', methods=['POST'])
@login_required
def backup_database():
    try:
        # 這裡實作資料庫備份邏輯
        # 可以使用 mysqldump 或其他備份工具
        
        backup_time = datetime.now()
        return jsonify({'status': 'success', 'backup_time': backup_time.isoformat()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)