import pandas as pd
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from .models import db, Admin, Order, OrderStatus  # 修改為相對導入
from .config import Config
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import plotly.express as px
import json
from codes.db import dbconfig, DB
from predict.models import Pred_total, Pred_sales
from predict.total_pred.predict_total_sales import Pred_Total_Sales
from predict.sales_pred.predict_sales_v4_2 import Pred_Sales
from weather_API.weather_API import weather_dict, classify_weather, get_weather_data, get_tomorrow_weather




from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object(Config)

# 儲存最新的天氣資訊(五分鐘會更新一次)
latest_weather = {
     "date": None,
     "weather": None,
     "temperature": None
     }

# 在 Config 類中添加上傳檔案配置
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 確保上傳目錄存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化資料庫
db.init_app(app)
db2 = DB(dbconfig())


# 初始化登入管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 確保這行存在
login_manager.login_message = '請先登入'  # 添加中文提示訊息

socketio = SocketIO(cors_allowed_origins="*")
socketio.init_app(app)

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
    try:
        print(f"收到更新訂單狀態請求: 訂單ID={order_id}")
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        new_status = data.get('status')
        
        print(f"嘗試將訂單狀態從 {order.status} 更新為 {new_status}")
        
        # 確保所有可能的狀態值都被接受
        all_statuses = [status.value for status in OrderStatus]
        print(f"有效的訂單狀態: {all_statuses}")
        
        if new_status not in all_statuses:
            return jsonify({'status': 'error', 'message': f'無效的狀態：{new_status}，有效狀態：{all_statuses}'}), 400

        old_status = order.status
        order.status = new_status
        db.session.commit()
        
        # 計算新的等候時間
        waiting_time = calculate_waiting_time()
        print(f"當前等候時間: {waiting_time}分鐘")
        
        # 如果訂單狀態更新為已完成，發送訂單完成消息
        if new_status == OrderStatus.COMPLETED.value:
            try:
                # 確保獲取到訂單號碼
                order_number = getattr(order, 'order_number', None)
                print(f"訂單號碼: {order_number}")
                
                # 如果沒有訂單號碼，使用訂單ID
                if not order_number:
                    order_number = f"A{order_id}"
                    print(f"使用替代訂單號碼: {order_number}")
                
                # 提取基本訂單號碼 (處理可能包含 - 的情況)
                if '-' in order_number:
                    base_number = order_number.split('-')[0]
                else:
                    base_number = order_number
                
                # 從基本訂單號碼中提取字母和數字部分
                if len(base_number) >= 6:  # MMDDA1 格式至少有6位
                    display_number = base_number[-2:]  # 只取字母和數字
                else:
                    display_number = base_number
                
                print(f"最終顯示的取餐號碼: {display_number}")
                
                # 發送事件
                socketio.emit('order_completed', {
                    'order_number': display_number,
                    'waiting_time': waiting_time
                })
                print(f"WebSocket 訊息已發送: 取餐號碼={display_number}, 等候時間={waiting_time}分鐘")
                        
            except Exception as e:
                print(f"發送訂單完成消息失敗: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            # 如果不是完成狀態，也發送等候時間更新
            try:
                socketio.emit('waiting_time_update', {
                    'waiting_time': waiting_time
                })
                print(f"等候時間已更新：{waiting_time}分鐘")
            except Exception as e:
                print(f"發送等候時間更新失敗: {str(e)}")
        
        return jsonify({'status': 'success', 'message': '訂單狀態已更新'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"更新訂單狀態時發生錯誤: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
        
#添加 API 端點用於初始加載等候時間
@app.route('/api/waiting-time', methods=['GET'])
def get_waiting_time():
    """獲取目前等候時間"""
    try:
        waiting_time = calculate_waiting_time()
        return jsonify({'waiting_time': waiting_time})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#後台計算等候時間的函數
def calculate_waiting_time():
    """計算目前等候時間（僅考慮未完成且未取消的訂單）"""
    # 只計算待處理和處理中的訂單
    active_count = Order.query.filter(
        Order.status.in_([OrderStatus.PENDING.value, OrderStatus.PROCESSING.value])
    ).count()
    waiting_minutes = round(active_count * 1.2, 1)  # 四捨五入到小數點後一位
    return waiting_minutes

# -----數據分析頁面------------------------------------------------------------

def get_sales_ranking(days): ## get_sales_ranking_query
    #{days}日內所有飲料銷售排名(包含銷售量為0商品)
    query = """
         SELECT
             m.drink_name,
             COALESCE(COUNT(o.drink_name), 0) AS total_sales
         FROM menu AS m
         LEFT JOIN orders AS o
             ON m.drink_name = o.drink_name
             AND o.order_date BETWEEN DATE_SUB(CURDATE(), INTERVAL %s DAY) AND CURDATE()
         GROUP BY m.drink_name
         ORDER BY total_sales DESC;
         """
    db2.connect()
    db2.execute(query=query, data=(days,))
    sales = db2.fetchall()
    # print(f"sales: {sales}")
    # db2.disconnect()
    db2.close()
    sales_dict = {item["drink_name"]: item["total_sales"] for item in sales}
    # print(f"sales_dict: {sales_dict}")
    return sales_dict

@app.route('/analytics')
@login_required
def analytics():
    return render_template("analytics.html")  # 這裡載入 analytics.html


@app.route("/api/weather", methods=["GET"])
def weather_api():
    station, location, weather, temperature = get_weather_data()
    return jsonify({
         "station": station,
         "location": location,
         "weather": weather,
         "temperature": temperature
         })

@app.route("/api/tomorrow_weather", methods=["GET"])
def tomorrow_weather():
    weather, max_temp, min_temp, date = get_tomorrow_weather()
    latest_weather.update({
                         "date": date,
                         "weather": classify_weather(weather=weather, weather_dict=weather_dict),
                         "temperature": round((max_temp + min_temp)/2),
                         })
    # print(latest_weather)
    return jsonify({
         "date": date,
         "weather": weather,
         "max_temp": max_temp,
         "min_temp": min_temp
         })

@app.route('/api/predict_sales', methods=['GET'])
def predict_sales():
    test_date = latest_weather['date']
    test_weather = latest_weather['weather']
    test_temperature = latest_weather['temperature']
    total_model_filename = "predict/total_pred/sales_total_model_v2_2025_03_18.pkl"
    # print(f"Model file path: {total_model_filename}")
    # print(f"1.{test_date} 2.{test_weather} 3.{test_temperature}")

    if not os.path.exists(total_model_filename):
        # print(f"Error: Model file not found at {total_model_filename}")
        return jsonify({"error": "Total sales model file not found"}), 500

    sales_model_filename = 'predict/sales_pred/lgbm_drink_weather_model_v4_2025_03_18.pkl'
    csv_filename = 'predict/new_data/drink_orders_2025_03_18.csv'
    # print("Creating Pred_total instance...")

    try:
        pred_total_info = Pred_total(
            date_string=test_date,
            weather=test_weather,
            temperature=test_temperature,
            model_filename=total_model_filename
        )
        predtotal = Pred_Total_Sales(pred_total_info)
        # print("Calling predtotal.pred()...")
        daily_total_sales = predtotal.pred()
        # print(f"Predicted total sales: {daily_total_sales}")

    except Exception as e:
        # print(f"Error in predtotal.pred(): {e}")
        return jsonify({"error": f"Prediction total sales failed: {str(e)}"}), 500
    # print("Creating Pred_sales instance...")

    try:
        pred_sales_info = Pred_sales(
            date_string=test_date,
            weather=test_weather,
            temperature=test_temperature,
            daily_total_sales=daily_total_sales,
            model_filename=sales_model_filename,
            csv_filename=csv_filename
        )

        predsales = Pred_Sales(pred_sales_info)
        # print("Calling predsales.get_top_6_sales_by_condition()...")
        weather_recommend = predsales.get_top_6_sales_by_condition()
        # print(f"Top 6 recommended drinks: {weather_recommend}")

    except Exception as e:
        print(f"Error in predsales.get_top_6_sales_by_condition(): {e}")
        return jsonify({"error": f"Prediction sales recommendation failed: {str(e)}"}), 500

    return jsonify({
        "daily_total_sales": daily_total_sales,
        "top_6_drinks": weather_recommend
    })

@app.route('/api/sales_chart')
def sales_chart():
    days = request.args.get("days", default=7, type=int)  # 取得輸入的天數
    sales_data = get_sales_ranking(days)
    # print(f"sales_data: {sales_data}")
    # 轉換為 DataFrame，確保所有品項都存在
    df = pd.DataFrame({'飲料名稱': list(sales_data.keys()), '銷量': list(sales_data.values())})

    df["銷量"] = pd.to_numeric(df["銷量"], errors="coerce").fillna(0).astype(int)
    # print(df["銷量"].describe())  # 看看是否範圍跑掉
    # print(df["銷量"].dtype)  # 確認資料型態

    df = df.sort_values(by="銷量", ascending=True)  # 銷量小的在最下方（橫向條狀圖）
    # print(df.columns)  # 應該輸出 Index(['飲料名稱', '銷量'], dtype='object')
    # print(df.dtypes)

    # 產生長條圖
    min_height = 300
    fig = px.bar(df, x="銷量", y="飲料名稱", orientation='h', 
                 title=f"過去 {days} 天的飲料銷售排名", color="銷量", 
                 height=max(min_height, 25 * len(df)))

    fig.update_layout(
        autosize=True,
        width=1200,  # 加寬圖形
        height=max(min_height, 25 * len(df)),  # 讓圖保持一定高度
        margin=dict(l=150, r=50, t=50, b=50),
        yaxis=dict(title="飲料名稱", tickfont=dict(size=14)),
        xaxis=dict(title="銷量", tickfont=dict(size=14))
    )

    graph_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    return Response(graph_html, mimetype="text/html")  # 回傳完整 HTML

#---數據分析頁面-以上--

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
    socketio.run(app, debug=True)
