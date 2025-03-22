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


@app.route('/analyze_chat', methods=['POST'])
def analyze_chat():
    """處理一般對話功能，通過 GPT API 判斷用戶意圖"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'status': 'error', 'message': '未提供文字'}), 400
        
        # 先嘗試直接使用訂單分析器處理
        try:
            # 預處理訂單文本
            processed_text = preprocess_order_text(text)
            
            # 直接使用訂單分析器嘗試分析
            app.logger.info(f"直接嘗試分析訂單: {processed_text}")
            order_details = analyzer.analyze_order(processed_text)
            
            # 如果成功解析為訂單
            if isinstance(order_details, list) and len(order_details) > 0:
                app.logger.info(f"成功解析訂單: {order_details}")
                
                # 為訂單詳情添加默認值
                for item in order_details:
                    if 'size' not in item or not item['size']:
                        item['size'] = '中杯'
                    if 'ice' not in item or not item['ice']:
                        item['ice'] = '正常冰'
                    if 'sugar' not in item or not item['sugar']:
                        item['sugar'] = '全糖'
                    if 'quantity' not in item:
                        item['quantity'] = 1
                
                # 將訂單格式化為易讀格式
                formatted_order = format_order_text(order_details)
                
                # 直接返回訂單信息
                return jsonify({
                    'status': 'success',
                    'is_order': True,
                    'reply': f"我幫您確認一下訂單：{formatted_order}\n\n請問確認訂購嗎？",
                    'order_details': order_details,
                    'order_text': formatted_order
                })
        except Exception as e:
            app.logger.info(f"直接訂單分析失敗: {str(e)}")
            # 如果直接分析失敗，繼續使用 GPT 分析
        
        # 使用 ChatAnalyzer (GPT API) 分析聊天內容和意圖
        gpt_result = chat_analyzer.analyze_chat(text)
        
        # 檢查 GPT 是否將意圖識別為訂單
        is_order_intent = gpt_result.get('intent') == 'order' or gpt_result.get('is_order_intent', False)
        
        app.logger.info(f"GPT 分析結果: 意圖={gpt_result.get('intent')}, 是否訂單={is_order_intent}")
        
        # 如果 GPT 判斷為點餐意圖，嘗試用訂單分析器處理
        if is_order_intent:
            app.logger.info(f"GPT 檢測到點餐意圖，處理訂單: {text}")
            
            # 使用訂單分析器分析訂單
            try:
                # 先預處理文本
                processed_text = preprocess_order_text(text)
                # 嘗試補充信息
                enhanced_text = enhance_order_text(processed_text)
                
                app.logger.info(f"預處理後的訂單文本: {enhanced_text}")
                order_details = analyzer.analyze_order(enhanced_text)
                
                # 檢查訂單分析結果
                if isinstance(order_details, list) and len(order_details) > 0:
                    # 成功解析訂單詳情
                    app.logger.info(f"GPT引導後成功解析訂單: {order_details}")
                    
                    # 為訂單詳情添加默認值
                    for item in order_details:
                        if 'size' not in item or not item['size']:
                            item['size'] = '中杯'
                        if 'ice' not in item or not item['ice']:
                            item['ice'] = '正常冰'
                        if 'sugar' not in item or not item['sugar']:
                            item['sugar'] = '全糖'
                        if 'quantity' not in item:
                            item['quantity'] = 1
                    
                    # 將訂單格式化為易讀格式
                    formatted_order = format_order_text(order_details)
                    
                    return jsonify({
                        'status': 'success',
                        'is_order': True,
                        'reply': f"我幫您確認一下訂單：{formatted_order}\n\n請問確認訂購嗎？",
                        'order_details': order_details,
                        'order_text': formatted_order
                    })
                else:
                    # 訂單分析失敗，但確認是訂單意圖
                    app.logger.info("GPT檢測為訂單意圖，但無法解析具體訂單")
                    return jsonify({
                        'status': 'success',
                        'is_order': True,
                        'reply': "看起來您想點餐，請告訴我您想要的飲料名稱、大小、甜度和冰量，例如：'一杯中杯半糖少冰珍珠奶茶'。",
                        'order_details': None
                    })
            except Exception as e:
                app.logger.error(f"GPT引導訂單分析失敗: {str(e)}")
                # 訂單分析出錯，但確認是訂單意圖
                return jsonify({
                    'status': 'success',
                    'is_order': True,
                    'reply': "很抱歉，我無法完全理解您的訂單。請明確說明想要的飲料名稱，以及甜度和冰量。",
                    'order_details': None
                })
        
        # 如果不是點餐意圖，返回 GPT 回應
        return jsonify({
            'status': 'success',
            'is_order': False,
            'reply': gpt_result.get('reply', '我不太理解您的意思，請再說一次。')
        })
    
    except Exception as e:
        app.logger.error(f"處理聊天分析時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'處理失敗: {str(e)}',
            'reply': '抱歉，系統暫時遇到問題，請稍後再試。'
        })


# 修改處理文字訂單的路由
@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                'status': 'error',
                'message': '請輸入訂單內容'
            })

        # 預處理文本 - 處理簡單訂單表達
        text = preprocess_order_text(text)
        
        # 使用訂單分析器分析訂單
        order_details = analyzer.analyze_order(text)
        
        # 檢查是否有錯誤
        if isinstance(order_details, dict) and 'status' in order_details and order_details['status'] == 'error':
            # 嘗試補充基本信息再次分析
            enhanced_text = enhance_order_text(text)
            if enhanced_text != text:
                print(f"增強訂單文本: {text} -> {enhanced_text}")
                order_details = analyzer.analyze_order(enhanced_text)
        
        # 如果仍然有錯誤，返回錯誤信息
        if isinstance(order_details, dict) and 'status' in order_details and order_details['status'] == 'error':
            return jsonify(order_details)
        
        # 確保返回的是列表
        if not isinstance(order_details, list):
            return jsonify({
                'status': 'error',
                'message': '訂單分析結果格式錯誤'
            })
        
        # 對於沒有明確指定的屬性，添加默認值
        for item in order_details:
            if 'size' not in item or not item['size']:
                item['size'] = '中杯'
            if 'ice' not in item or not item['ice']:
                item['ice'] = '正常冰'
            if 'sugar' not in item or not item['sugar']:
                item['sugar'] = '全糖'
            if 'quantity' not in item:
                item['quantity'] = 1
        
        return jsonify({
            'status': 'success',
            'order_details': order_details
        })

    except Exception as e:
        print(f"處理訂單時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': '處理訂單時發生錯誤'
        })

# 預處理訂單文本
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
# 修改確認訂單的路由，確保發送 Socket.IO 通知
@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    try:
        data = request.json
        order_details = data.get('order_details', [])
        
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
        
        # 生成訂單號碼
        order_numbers = generate_order_number(db, len(expanded_orders))
        if not order_numbers:
            return jsonify({'status': 'error', 'message': '無法生成訂單號碼'})
        
        # 取得當前時間
        now = datetime.now()
        order_date = now.date()
        order_time = now.strftime('%H:%M:%S')
        
        success_count = 0
        created_order_numbers = []
        
        for i, order in enumerate(expanded_orders):
            try:
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
                    'pending', order_numbers[i]
                )
                
                print(f"準備插入訂單，值為: {values}")
                if db.execute(query, values):
                    success_count += 1
                    created_order_numbers.append(order_numbers[i])
                    
                    # 使用 Socket.IO 廣播訂單狀態
                    socketio.emit('order_status_update', {
                        'order_number': order_numbers[i],
                        'status': 'pending',
                        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
                    })
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
            
        return jsonify({
            'status': 'success',
            'message': f'成功建立 {success_count}/{len(expanded_orders)} 筆訂單',
            'order_number': order_numbers[0].split('-')[0][-2:] if '-' in order_numbers[0] else order_numbers[0][-2:],  # 只返回第一杯飲料號碼的最後兩位
            'full_order_number': order_numbers[0]   # 完整訂單號碼，用於追蹤
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