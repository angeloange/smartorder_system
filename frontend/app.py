from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import os
import datetime
from datetime import datetime
from enum import Enum
import speech_recognition as sr
from pydub import AudioSegment
from codes.db import DB, dbconfig
from predict.models import Pred_total, Pred_sales
from predict.total_pred.predict_total_sales import Pred_Total_Sales
from predict.sales_pred.predict_sales_v4_2 import Pred_Sales
from tools.tools import convert_order_date_for_db, get_now_time
from .order_analyzer import OrderAnalyzer
from weather_API.weather_API import weather_dict ,classify_weather, get_weather_data
from flask_socketio import SocketIO  # 添加這行
from frontend.codes.speech import speech_bp
from chat_tools.chat_analyzer import ChatAnalyzer


# 初始化 Flask 應用
app = Flask(__name__)
chat_analyzer = ChatAnalyzer()
# 初始化資料庫連接
db = DB(dbconfig())

# 初始化訂單分析器
analyzer = OrderAnalyzer()

socketio = SocketIO(cors_allowed_origins="*")
socketio.init_app(app)


# 定義 Enum 類型
class Size(Enum):
    LARGE = '大杯'
    SMALL = '小杯'

class SugarType(Enum):
    FULL = 'full'        # 全糖
    SEVENTY = 'seventy'  # 七分糖
    HALF = 'half'        # 半糖
    THIRTY = 'thirty'    # 三分糖
    LIGHT = 'light'      # 微糖
    FREE = 'free'        # 無糖

# 在 Enum 類別定義後添加映射
SUGAR_MAPPING = {
    '全糖': 'full',
    '七分糖': 'seventy',
    '半糖': 'half',
    '微糖': 'light',
    '無糖': 'free'
}

# 在 Enum 類別定義後添加轉換映射
ICE_MAPPING = {
    '正常冰': 'iced',
    '少冰': 'less',
    '微冰': 'light',
    '去冰': 'no_ice',
    '熱飲': 'hot',
    '常溫': 'room'
}

SUGAR_MAPPING = {
    '全糖': 'full',
    '少糖': 'seventy',
    '半糖': 'half',
    '微糖': 'light',
    '無糖': 'free'
}
class WeatherStatus(Enum):
    SUNNY = 'sunny'
    CLOUDY = 'cloudy'
    RAINY = 'rainy'
    STORMY = 'stormy'


# 註冊藍圖
app.register_blueprint(speech_bp)

# 添加路由讓靜態檔案可以被訪問
@app.route('/temp_audio/<path:filename>')
def temp_audio(filename):
    # 確保使用絕對路徑
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_audio')
    return send_from_directory(audio_dir, filename)

@app.route('/')
def index():
    return render_template('index.html')

def format_order_text(order_details):
    """格式化訂單詳情為人類可讀文本"""
    order_text = []
    for item in order_details:
        parts = []
        if 'size' in item and item['size']: parts.append(item['size'])
        if 'sugar' in item and item['sugar']: parts.append(item['sugar'])
        if 'ice' in item and item['ice']: parts.append(item['ice'])
        parts.append(item['drink_name'])
        
        text = ''.join(parts)
        if 'quantity' in item and item['quantity'] > 1:
            text += f" {item['quantity']}杯"
        order_text.append(text)
    
    return '、'.join(order_text)

@app.route('/analyze_chat', methods=['POST'])
def analyze_chat():
    try:
        data = request.json
        text = data.get('text', '')
        
        app.logger.info(f"處理聊天輸入: '{text}'")
        
        # 使用 OpenAI 判斷意圖
        chat_result = chat_analyzer.analyze_chat(text)
        app.logger.info(f"OpenAI 意圖判斷結果: {chat_result}")
        
        # 修正這一行 - 使用正確的變數名
        order_result = analyzer.analyze_order(text)  # 使用 analyzer 而非 order_analyzer
        app.logger.info(f"訂單分析結果: {order_result}")
        
        # 如果訂單分析成功（有結果）
        if isinstance(order_result, list) and len(order_result) > 0:
            order_text = format_order_text(order_result)
            return jsonify({
                'status': 'success',
                'is_order': True,
                'reply': f"我幫您確認一下訂單：{order_text}\n\n請問確認訂購嗎？",
                'order_details': order_result
            })
        
        # 否則使用聊天回應
        return jsonify({
            'status': 'success',
            'is_order': chat_result.get('is_order_intent', False),
            'reply': chat_result.get('reply', "抱歉，我不太明白您的意思。"),
            'order_details': []
        })
    except Exception as e:
        app.logger.error(f"處理聊天時出錯: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"處理失敗: {str(e)}",
            'reply': "抱歉，系統暫時遇到問題，請稍後再試。"
        })
# 修改處理文字訂單的路由
def preprocess_order_text(text):
    # 檢查是否是純飲料名稱，例如："蜂蜜檸檬"
    for drink in analyzer.drinks_menu:
        if text.strip() == drink:
            return f"一杯{text}"
    
    return text

# 增強訂單文本 - 針對缺少的資訊進行補充
def enhance_order_text(text):
    # 如果文本只有飲料名稱，加上數量
    if len(text) < 10 and not any(x in text for x in ['杯', '要', '點']):
        return f"一杯{text}"
    
    # 已經有基本結構，但可能缺少屬性
    enhanced = text
    
    # 檢查是否需要添加甜度
    if not any(sugar in enhanced for sugar in analyzer.sugar_options):
        enhanced += " 全糖"
    
    # 檢查是否需要添加冰量
    if not any(ice in enhanced for ice in analyzer.ice_options):
        enhanced += " 正常冰"
    
    return enhanced

# 新增月度熱銷飲品路由
# 初始化資料庫連接
try:
    db = DB(dbconfig())
    db.connect()  # 確保建立連接
except Exception as e:
    print(f"資料庫連接失敗: {str(e)}")
    db = None

@app.route('/monthly_top_drinks')
def monthly_top_drinks():
    try:
        if not db:
            raise Exception("資料庫連接未初始化")
            
        # 取得當前月份的第一天
        today = datetime.now()
        first_day = datetime(today.year, today.month, 1)
        
        # 查詢本月熱銷飲品
        query = """
            SELECT drink_name, COUNT(*) as count 
            FROM orders 
            WHERE DATE(created_at) >= DATE(%s)
            GROUP BY drink_name 
            ORDER BY count DESC 
            LIMIT 3
        """
        
        # 使用 connect() 確保每次查詢都有連接
        db.connect()
        
        # 執行查詢
        if db.execute(query, (first_day.strftime('%Y-%m-%d'),)):
            results = db.fetchall()
            print(f"查詢結果: {results}")  # 除錯用
            
            return jsonify({
                'status': 'success',
                'data': [
                    {'name': row['drink_name'], 'count': row['count']}
                    for row in results
                ]
            })
        else:
            raise Exception("查詢執行失敗")
            
    except Exception as e:
        print(f"獲取熱銷飲品時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'success',
            'data': [
                {'name': '尚無資料', 'count': 0}
            ]
        })

@app.route('/api/weather_recommend', methods=['GET'])
def weather_recommend():
    station, location, weather, temperature = get_weather_data()
    date = str(datetime.now().date())

    test_date = date
    test_weather = classify_weather(weather=weather, weather_dict=weather_dict)
    test_temperature = int(temperature)
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

    return jsonify(weather_recommend)


def get_last_order_number(db_instance):
    """獲取今天最後一筆訂單號碼"""
    try:
        today = datetime.now().strftime('%m%d')
        query = """
            SELECT order_number 
            FROM orders 
            WHERE order_number LIKE %s
            AND DATE(created_at) = CURDATE()
            ORDER BY order_number DESC 
            LIMIT 1
        """
        result = db_instance.fetchone(query, (f"{today}%",))
        return result['order_number'] if result else None
    except Exception as e:
        print(f"獲取最後訂單號碼時發生錯誤: {str(e)}")
        return None

def generate_order_number(db, count=1):
    """生成新的訂單號碼，確保唯一性"""
    import random
    import time
    today = datetime.now().strftime('%m%d')
    # 生成所有訂單號碼
    order_numbers = []
    max_attempts = 5
    for i in range(count):
        # 在每個循環中重新查詢最後訂單號，確保最新
        last_number = get_last_order_number(db)
        attempts = 0
        while attempts < max_attempts:
            # 基本號碼生成邏輯
            if not last_number:
                letter = chr(65 + random.randint(0, 25))  # A-Z隨機一個字母
                number = random.randint(1, 9)  # 1-9隨機一個數字
                base_number = f'{today}{letter}{number}'
            else:
                # 從完整訂單號碼中提取字母和數字
                if '-' in last_number:
                    base_last = last_number.split('-')[0]
                else:
                    base_last = last_number
                # 提取字母和數字部分，但增加隨機性
                letter = chr(65 + random.randint(0, 25))  # 隨機字母代替遞增
                number = random.randint(1, 9)  # 隨機數字
                base_number = f'{today}{letter}{number}'
            # 添加時間戳微秒部分作為唯一標識
            unique_suffix = str(int(time.time() * 1000) % 10000)
            new_number = f"{base_number}-{unique_suffix}"
            
            # 檢查訂單號是否已存在
            query = "SELECT 1 FROM orders WHERE order_number = %s LIMIT 1"
            result = db.fetchone(query, (new_number,))
            if not result:
                # 訂單號不存在，可以使用
                order_numbers.append(new_number)
                break
            attempts += 1
            # 短暫延遲以避免時間戳完全相同
            time.sleep(0.01)
        if attempts >= max_attempts:
            # 如果嘗試多次仍失敗，使用更長的隨機字符串
            fallback = f"{today}{chr(65 + random.randint(0, 25))}{random.randint(1, 9)}-{str(uuid.uuid4())[:8]}"
            order_numbers.append(fallback)
    return order_numbers

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    """確認訂單並生成訂單號碼"""
    try:
        data = request.json
        order_details = data.get('order_details', [])
        order_details = convert_order_date_for_db(orders_list=order_details)
        if not order_details:
            return jsonify({'status': 'error', 'message': '訂單不能為空'})
        
        # 展開訂單項目，處理相同品項多杯的情況
        expanded_orders = []
        for order in order_details:
            # 獲取數量，預設為1
            quantity = order.get('quantity', 1)
            quantity = int(quantity)  # 確保是整數
            
            # 根據數量複製訂單項目
            for i in range(quantity):
                # 創建新的訂單項目，但不包含 quantity
                order_item = {k: v for k, v in order.items() if k != 'quantity'}
                expanded_orders.append(order_item)
        
        # 生成符合規定的訂單號碼
        base_order_number = generate_order_number(db, len(expanded_orders))
        if not base_order_number:
            return jsonify({'status': 'error', 'message': '無法生成訂單號碼'})
        
        # 取得當前時間
        now = datetime.now()
        order_date = now.date()
        order_time = now.strftime('%H:%M:%S')
        success_count = 0
        created_order_numbers = []
        
        # 為每一個展開的訂單分配序號
        for i, order in enumerate(expanded_orders):
            try:
                # 生成最終訂單號碼：基礎號碼 + "-" + 序號
                item_order_number = f"{base_order_number}-{i+1}"
                query = """
                    INSERT INTO orders (
                        drink_name, size, ice_type, sugar_type, 
                        order_date, order_time, 
                        weather_status, temperature,
                        status, created_at, order_number
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                """
                values = (
                    order.get('drink_name', '未知飲品'), 
                    order.get('size', '中杯'),
                    order.get('ice', '正常冰'), 
                    order.get('sugar', '全糖'), 
                    order_date, order_time, 
                    'sunny', 25.0,  # 默認天氣
                    'pending', item_order_number
                )
                
                print(f"準備插入訂單，值為: {values}")
                if db.execute(query, values):
                    success_count += 1
                    created_order_numbers.append(item_order_number)
                    
                    # 使用 Socket.IO 廣播訂單狀態 - 狀態為 pending
                    socketio.emit('order_status_update', {
                        'order_number': item_order_number,
                        'status': 'pending',
                        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    # 在開發環境中，自動模擬訂單狀態變更
                    # 實際生產環境應該由後台管理系統觸發
                    if app.config.get('ENV') == 'development':
                        # 2秒後狀態變為 preparing
                        socketio.sleep(2)
                        socketio.emit('order_status_update', {
                            'order_number': item_order_number,
                            'status': 'preparing',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        # 再過6秒後狀態變為 completed
                        def send_completed_status(order_number):
                            socketio.sleep(6)
                            socketio.emit('order_completed', {
                                'order_number': order_number,
                                'status': 'completed',
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                            # 更新數據庫狀態
                            update_query = "UPDATE orders SET status = 'completed' WHERE order_number = %s"
                            db.execute(update_query, (order_number,))
                            
                            print(f"訂單 {order_number} 已完成")
                            
                        # 啟動背景任務發送完成通知
                        socketio.start_background_task(send_completed_status, item_order_number)
                else:
                    print(f"插入訂單失敗: {values}")
            except Exception as e:
                print(f"插入單筆訂單時發生錯誤: {str(e)}")
        
        if success_count == 0:
            return jsonify({
                'status': 'error',
                'message': '所有訂單儲存失敗'
            })
        
        # 輸出所有創建的訂單號碼，方便調試
        print(f"成功創建訂單: {created_order_numbers}")
        
        # 提取顯示用的取餐號碼 (基礎訂單號的最後2位)
        display_number = base_order_number[-2:] if len(base_order_number) >= 2 else base_order_number
            
        return jsonify({
            'status': 'success',
            'message': f'訂單已確認！您的訂單正在製作中，預計等候時間約 3 分鐘。您的取餐號碼為 {display_number}。',
            'order_number': display_number,
            'full_order_number': base_order_number  # 完整訂單號碼，用於追蹤
        })
    
    except Exception as e:
        print(f"儲存訂單時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '訂單處理失敗'
        })

if __name__ == '__main__':
    app.run(debug=True)