from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from order_analyzer import OrderAnalyzer
import json
import os
import datetime
from datetime import datetime
from config import Config
from enum import Enum
from flask import Flask

from codes.db import DB, dbconfig
from tools.tools import convert_order_date_for_db, get_now_time


#--
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)

db = DB(dbconfig())

# 初始化 OrderAnalyzer
analyzer = OrderAnalyzer()

class Size(Enum):
    LARGE = '大杯'
    SMALL = '小杯'

class IceType(Enum):
    ICED = 'iced'
    HOT = 'hot'
    ROOM_TEMP = 'room_temp'

class SugarType(Enum):
    FULL = 'full'
    HALF = 'half'
    FREE = 'free'

class WeatherStatus(Enum):
    SUNNY = 'sunny'
    CLOUDY = 'cloudy'
    RAINY = 'rainy'
    STORMY = 'stormy'



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        # 修改這裡：使用實例方法而不是類別方法
        order_details = analyzer.analyze_order(text)
        
        if isinstance(order_details, dict) and 'status' in order_details:
            return jsonify(order_details)
        
        return jsonify({
            'status': 'success',
            'speech_text': text,
            'order_details': order_details
        })
    except Exception as e:
        print(f"分析文字時發生錯誤：{str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    try:
        data = request.json
        #{'order_details': [{'drink_name': '綠茶', 'ice': '微冰', 'quantity': 1, 'size': '小杯', 'sugar': '無糖'}], 'speech_text': '一杯小杯綠茶無糖微冰'}
        print(f"收到訂單資料：{data}")

        date, time = get_now_time()

        # 處理每個飲料訂單
        for order_item in data['order_details']:
            # 確保所有欄位都有正確的格式
            ice_type = order_item['ice'].upper()             #???????????????
            sugar_type = order_item['sugar'].upper()         #???????????????
            size = order_item.get('size', '大杯')   #GPT可以當下處理？

        orders_list = convert_order_date_for_db(orders_list=data['order_details'])

           #天氣資訊待氣象API確認後才做連接#裝置及地點功能尚未設置
        weather_status = 'sunny'
        temperature = 22
           #之前提到的裝置跟地點，之後看有沒有機會實現？ 目前先寫死
        device_id = "IPHONE 101"
        location_name = "台中店"
           # 有設計電話儲存後再接進來
        phone_number = None

        orders_query = """
             INSERT INTO orders (
             drink_name, size, ice_type, sugar_type, order_date,
             order_time, weather_status, temperature, phone_number)
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
             """

        order_locations_query = """
             INSERT INTO order_locations (
             order_id, device_id, location_name)
             VALUES (%s, %s, %s)
             """

        db.connect()
        for drink in orders_list:
            for q in range(drink['quantity']):
                orders_data = (drink['drink_name'], drink['size'], drink['ice'],
                        drink['sugar'], date, time, weather_status, temperature, phone_number)

                db.execute(query=orders_query, data=orders_data)
                order_id = db.cursor.lastrowid
                print(f"新增訂單，order_id為: {order_id}")
                order_locations_data = (order_id, device_id, location_name)
                db.execute(query=order_locations_query, data=order_locations_data)
                print(f"成功紀錄 訂單編號 {order_id} 的裝置及地點 至 order_locations 表格。")

        db.disconnect()    
        print("訂單已儲存到資料庫")
        
        return jsonify({
             'status': 'success',
             'message': '訂單已確認並儲存'
             })
    except Exception as e:
        print(f'連線失敗: {e}')
        db.roll_back()
        db.disconnect()
        return jsonify({
             'status': 'error',
             'message': str(e)
             })


# # 新增熱銷排行API
# @app.route('/monthly_top_drinks')
# def get_monthly_top_drinks():
#     try:
#         # 從資料庫查詢熱銷飲品
#         result = db.session.execute("""
#             SELECT drink_name, COUNT(*) as count 
#             FROM orders 
#             WHERE order_time >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
#             GROUP BY drink_name 
#             ORDER BY count DESC 
#             LIMIT 5
#         """)
        
#         top_drinks = [{'drink_name': row[0], 'count': row[1]} for row in result]
        
#         return jsonify({
#             'status': 'success',
#             'data': top_drinks
#         })
#     except Exception as e:
#         return jsonify({
#             'status': 'error',
#             'message': str(e)
#         })

@app.route('/synthesize_speech', methods=['POST'])
def synthesize_speech():
    try:
        data = request.json
        text = data.get('text', '')
        
        # 這裡可以使用不同的TTS服務，例如：
        # 1. Google Cloud Text-to-Speech
        # 2. Azure Cognitive Services
        # 3. Amazon Polly
        # 實作細節取決於選擇的服務
        
        return jsonify({
            'status': 'success',
            'audio_url': 'path_to_audio_file'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5002)