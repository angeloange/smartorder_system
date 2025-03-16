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
import speech_recognition as sr
from pydub import AudioSegment
import os

app = Flask(__name__)

db = DB(dbconfig())

# 初始化訂單分析器
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
        
        # 使用OrderAnalyzer進行分析
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
        
        db.session.commit()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"已建立訂單記錄，時間: {current_time}")

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

# 確保臨時音訊檔案夾存在
UPLOAD_FOLDER = 'temp_audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    try:
        if 'audio' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未收到音訊檔案'
            }), 400

        audio_file = request.files['audio']
        
        # 儲存並處理音訊檔案
        temp_webm = os.path.join(UPLOAD_FOLDER, 'temp_audio.webm')
        audio_file.save(temp_webm)

        # 轉換為 WAV 格式
        temp_wav = os.path.join(UPLOAD_FOLDER, 'temp_audio.wav')
        audio = AudioSegment.from_file(temp_webm)
        audio.export(temp_wav, format="wav")

        # 進行語音辨識
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='zh-TW')

        print(f"辨識結果: {text}")  # 除錯用
        
        # 分析訂單
        order_details = analyzer.analyze_order(text)
        print(f"訂單分析: {order_details}")  # 除錯用

        # 清理臨時檔案
        if os.path.exists(temp_webm):
            os.remove(temp_webm)
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

        return jsonify({
            'status': 'success',
            'speech_text': text,
            'order_details': order_details
        })

    except sr.UnknownValueError:
        return jsonify({
            'status': 'error',
            'message': '無法辨識語音內容'
        })
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'處理時發生錯誤: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, port=5005)