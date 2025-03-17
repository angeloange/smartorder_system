from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
from models import db, Order, Admin, Product

app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = 'your-secret-key'  # 請更改為安全的密鑰

db.init_app(app)

# 登入要求裝飾器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_name'] = admin.name
            admin.last_login = datetime.now()
            db.session.commit()
            return redirect(url_for('dashboard'))
        
        flash('帳號或密碼錯誤', 'danger')
    return render_template('login.html')

@app.route('/')
@login_required
def dashboard():
    today = datetime.now().date()
    stats = {
        'today_orders': Order.query.filter(Order.order_date == today).count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'recent_orders': Order.query.order_by(Order.order_time.desc()).limit(5).all()
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = Order.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.order_time.desc()).paginate(page=page, per_page=20)
    return render_template('orders.html', orders=orders, current_status=status)

@app.route('/api/orders/update_status', methods=['POST'])
@login_required
def update_order_status():
    data = request.get_json()
    order = Order.query.get_or_404(data['order_id'])
    order.status = data['status']
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/products')
@login_required
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/analytics')
@login_required
def analytics():
    # ... 分析相關代碼 ...
    return render_template('analytics.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5003)
