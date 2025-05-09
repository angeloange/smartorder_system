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
from tools.load_path import LoadPath
from tools.tools import convert_order_date_for_db, get_now_time
from .order_analyzer import OrderAnalyzer
from weather_API.weather_API import weather_dict ,classify_weather, get_weather_data
from flask_socketio import SocketIO  # 添加這行
from frontend.codes.speech import speech_bp
from chat_tools.chat_analyzer import ChatAnalyzer
import re


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


# 在 app.py 中添加此路由
@app.route('/azure_credentials')
def azure_credentials():
    """提供 Azure 語音服務憑證給前端"""
    # 從環境變數獲取 Azure 憑證
    key = os.environ.get('AZURE_SPEECH_KEY', '')
    region = os.environ.get('AZURE_SPEECH_REGION', 'eastasia')
    
    if key:
        app.logger.info('成功提供 Azure 語音憑證')
    else:
        app.logger.warning('未找到 Azure 語音憑證')
    
    return jsonify({
        'key': key,
        'region': region
    })

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
    
def fallback_recommendation():
    try:
        station, location, weather, temperature = get_weather_data()
        date = str(datetime.now().date())

        test_date = date
        test_weather = classify_weather(weather=weather, weather_dict=weather_dict)
        test_temperature = int(temperature)
        
        # 使用簡單推薦邏輯
        weather_lower = test_weather.lower()
        drinks = []
        
        # 根據溫度選擇飲品
        if test_temperature > 28:  # 炎熱
            drinks = ["珍珠奶茶", "檸檬綠茶", "百香果綠茶", "蜂蜜檸檬", "芒果冰沙", "冬瓜茶"]
        elif test_temperature > 22:  # 溫暖
            drinks = ["波霸奶茶", "椰果奶茶", "蜂蜜奶茶", "烏龍拿鐵", "冬瓜檸檬", "青茶"]
        elif test_temperature > 15:  # 涼爽
            drinks = ["焦糖奶茶", "巧克力牛奶", "可可", "拿鐵咖啡", "牛奶咖啡", "摩卡咖啡"]
        else:  # 寒冷
            drinks = ["熱拿鐵", "熱奶茶", "黑糖珍珠鮮奶", "熱可可", "熱烏龍茶", "熱紅茶"]
        
        # 根據天氣進一步調整
        if weather_lower == "rainy" or weather_lower == "stormy":
            # 下雨天適合的飲品
            if test_temperature <= 20:
                drinks = ["熱拿鐵", "熱奶茶", "黑糖珍珠鮮奶", "熱可可", "熱烏龍茶", "熱紅茶"]
        
        return jsonify(drinks)
    except Exception as e:
        print(f"天氣推薦功能錯誤: {str(e)}")
        # 返回預設推薦
        return jsonify(["珍珠奶茶", "波霸奶茶", "烏龍拿鐵", "檸檬綠茶", "焦糖奶茶", "蜂蜜奶茶"])
    
@app.route('/api/weather_recommend', methods=['GET'])
def weather_recommend():
    try:
        station, location, weather, temperature = get_weather_data()
        date = str(datetime.now().date())

        test_date = date
        test_weather = classify_weather(weather=weather, weather_dict=weather_dict)
        test_temperature = int(temperature)

        total_model_filename = "sales_total_model_v2_2025_03_18.pkl"
        sales_model_filename = "lgbm_drink_weather_model_v4_2025_03_18.pkl"
        sales_csv_filename = "drink_orders_2025_03_18.csv"
        load_path = LoadPath(total_model_filename=total_model_filename,
                             sales_model_filename=sales_model_filename,
                             sales_csv_filename=sales_csv_filename
                             )
        total_model_filename = load_path.load_total_model_path()
        sales_model_filename = load_path.load_sales_model_path()
        sales_csv_filename = load_path.load_sales_csv_path()

        missing_files = [
             filename for filename in [total_model_filename, sales_model_filename, sales_csv_filename]
                 if not os.path.exists(filename)
                 ]
        if missing_files:
            print(f"錯誤: 未找到以下檔案 {', '.join(missing_files)}")
            return fallback_recommendation()

        pred_total_info = Pred_total(
            date_string=test_date,
            weather=test_weather,
            temperature=test_temperature,
            model_filename=total_model_filename
            )
        predtotal = Pred_Total_Sales(pred_total_info)
        daily_total_sales = predtotal.pred()
        pred_sales_info = Pred_sales(
            date_string=test_date,
            weather=test_weather,
            temperature=test_temperature,
            daily_total_sales=daily_total_sales,
            model_filename=sales_model_filename,
            csv_filename=sales_csv_filename
            )
        predsales = Pred_Sales(pred_sales_info)
        weather_recommend = predsales.get_top_6_sales_by_condition()

        return jsonify(weather_recommend)
    except Exception as e:
        print(f"天氣推薦菜單異常: {e}")
        return fallback_recommendation()

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
    """生成新的訂單號碼，確保唯一性和序列性"""
    
    today = datetime.now().strftime('%m%d')
    
    # 獲取最後一筆訂單號碼
    last_number = get_last_order_number(db)
    
    # 確定下一個字母和數字
    if not last_number or not last_number.startswith(today):
        # 今天第一筆訂單，從 A1 開始
        letter = 'A'
        number = 1
    else:
        try:
            # 從訂單號提取字母和數字部分
            base_part = last_number.split('-')[0] if '-' in last_number else last_number
            pattern = r'\d{4}([A-Z])(\d)'
            match = re.search(pattern, base_part)
            
            if match:
                letter = match.group(1)  # 字母部分
                number = int(match.group(2))  # 數字部分
                
                # 計算下一個字母和數字
                number += 1
                if number > 9:
                    number = 1
                    letter = chr(ord(letter) + 1)
                    # 如果超過Z，回到A
                    if letter > 'Z':
                        letter = 'A'
            else:
                # 匹配失敗，使用默認值
                letter = 'A'
                number = 1
        except Exception as e:
            print(f"解析訂單號時出錯: {str(e)}, 使用默認值")
            letter = 'A'
            number = 1
    
    # 基礎訂單號
    base_order_number = f"{today}{letter}{number}"
    
    # 生成所有訂單號碼（依據杯數添加後綴）
    order_numbers = []
    for i in range(count):
        item_order_number = f"{base_order_number}-{i+1}"
        order_numbers.append(item_order_number)
    
    return base_order_number, order_numbers


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
        base_order_number, item_order_numbers = generate_order_number(db, len(expanded_orders))
        if not base_order_number:
            return jsonify({'status': 'error', 'message': '無法生成訂單號碼'})
        display_number = base_order_number[4:] if len(base_order_number) >= 6 else base_order_number

        # 取得當前時間
        now = datetime.now()
        order_date = now.date()
        order_time = now.strftime('%H:%M:%S')
        success_count = 0
        created_order_numbers = []
        
        # 安全獲取天氣數據
        try:
            weather_data = get_weather_data()
            
            # 檢查返回值結構
            if isinstance(weather_data, tuple) and len(weather_data) >= 4:
                # 正常格式：函數返回4個值
                weather = classify_weather(weather=weather_data[2], weather_dict=weather_dict)
                temperature = weather_data[3]
            else:
                # API 返回格式已變更：使用預設值
                print(f"天氣 API 返回異常格式: {weather_data}")
                weather = "sunny"  # 預設天氣
                temperature = 25  # 預設溫度
        except Exception as e:
            print(f"獲取天氣數據時出錯: {str(e)}")
            # 發生錯誤時使用預設值
            weather = "sunny"
            temperature = 25
        
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
                    order.get('size', '大杯'),
                    order.get('ice', '正常冰'), 
                    order.get('sugar', '全糖'), 
                    order_date, order_time, 
                    weather, temperature,
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