from flask import Flask, render_template, jsonify, request
import json
import os
import datetime
from datetime import datetime
from enum import Enum
import speech_recognition as sr
from pydub import AudioSegment

from codes.db import DB, dbconfig
from tools.tools import convert_order_date_for_db, get_now_time
from order_analyzer import OrderAnalyzer

# 初始化 Flask 應用
app = Flask(__name__)

# 初始化資料庫連接
db = DB(dbconfig())

# 初始化訂單分析器
analyzer = OrderAnalyzer()

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
    '三分糖': 'thirty',
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


@app.route('/')
def index():
    return render_template('index.html')

# 新增處理文字訂單的路由
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

        # 使用訂單分析器分析訂單
        order_details = analyzer.analyze_order(text)
        
        if isinstance(order_details, dict) and 'status' in order_details and order_details['status'] == 'error':
            return jsonify(order_details)
        
        return jsonify({
            'status': 'success',
            'order_details': order_details
        })

    except Exception as e:
        print(f"處理訂單時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '處理訂單時發生錯誤'
        })

# 新增月度熱銷飲品路由
@app.route('/monthly_top_drinks')
def monthly_top_drinks():
    try:
        # 取得當前月份的第一天和最後一天
        today = datetime.now()
        first_day = datetime(today.year, today.month, 1)
        
        # 查詢本月熱銷飲品
        query = """
            SELECT drink_name, COUNT(*) as count 
            FROM orders 
            WHERE order_date >= %s 
            GROUP BY drink_name 
            ORDER BY count DESC 
            LIMIT 5
        """
        
        results = db.fetch_all(query, (first_day,))
        
        return jsonify({
            'status': 'success',
            'data': [
                {'name': row['drink_name'], 'count': row['count']}
                for row in results
            ]
        })
    except Exception as e:
        print(f"獲取熱銷飲品時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '獲取熱銷飲品失敗'
        })

# 新增確認訂單路由
@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    try:
        data = request.get_json()
        order_details = data.get('order_details', [])
        
        now = datetime.now()
        weather_status = WeatherStatus.SUNNY.value
        
        for order in order_details:
            # 使用映射轉換冰塊和糖度
            ice_type = ICE_MAPPING.get(order.get('ice', '正常冰'), 'iced')
            sugar_type = SUGAR_MAPPING.get(order.get('sugar', '全糖'), 'full')
            
            query = """
                INSERT INTO orders (
                    drink_name, size, ice_type, sugar_type,
                    order_date, order_time, weather_status,
                    temperature, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                order['drink_name'],
                order.get('size', Size.SMALL.value),
                ice_type,
                sugar_type,
                now.date(),
                now.time(),
                weather_status,
                25.0,
                now
            )
            
            print(f"Inserting order with values: {values}")  # 除錯訊息
            
            if not db.execute(query, values):
                raise Exception("訂單儲存失敗")

        return jsonify({
            'status': 'success',
            'message': '訂單已成功建立'
        })

    except Exception as e:
        print(f"儲存訂單時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '儲存訂單失敗'
        })
if __name__ == '__main__':
    app.run(debug=True)