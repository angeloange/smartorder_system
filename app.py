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
from flask_sqlalchemy import SQLAlchemy
from config import Config
import speech_recognition as sr
from pydub import AudioSegment
import os

app = Flask(__name__)
app.config.from_object(Config)

# 重新初始化資料庫連線
db = SQLAlchemy()
db.init_app(app)

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

class VoiceOrder(db.Model):
    __tablename__ = 'orders'  # 改用正確的資料表名稱
    
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drink_name = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Enum(Size), nullable=False, default=Size.SMALL)
    ice_type = db.Column(db.Enum(IceType), nullable=False, default=IceType.ROOM_TEMP)
    sugar_type = db.Column(db.Enum(SugarType), nullable=False, default=SugarType.HALF)
    order_date = db.Column(db.Date, default=datetime.utcnow().date)
    order_time = db.Column(
        db.TIMESTAMP, 
        server_default=db.func.current_timestamp(),
        nullable=False
    )
    weather_status = db.Column(db.Enum(WeatherStatus), nullable=False, default=WeatherStatus.CLOUDY)
    temperature = db.Column(db.Numeric(4,2), nullable=False, default=20.00)
    phone_number = db.Column(db.CHAR(10), nullable=True)

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
        current_time = datetime.now()  # 獲取當前時間
        
        # 處理每個飲料訂單
        for order_item in data['order_details']:
            new_order = VoiceOrder(
                drink_name=order_item['drink_name'],
                size=order_item.get('size', '中杯'),
                ice_type=order_item['ice'],
                sugar_type=order_item['sugar'],
                order_date=current_time.date(),    # 設置訂單日期
                order_time=current_time,           # 設置訂單時間
                phone_number=data.get('phone_number')
            )
            db.session.add(new_order)
            print(f"新增訂單: {order_item}, 時間: {current_time}")
        
        db.session.commit()
        print(f"已建立訂單記錄，時間: {current_time}")

        return jsonify({
            'status': 'success',
            'message': '訂單已確認並儲存',
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        db.session.rollback()
        print(f"儲存訂單時發生錯誤：{str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'儲存訂單時發生錯誤: {str(e)}'
        })

# 新增熱銷排行API
@app.route('/monthly_top_drinks')
def get_monthly_top_drinks():
    try:
        # 從資料庫查詢熱銷飲品
        result = db.session.execute("""
            SELECT drink_name, COUNT(*) as count 
            FROM orders 
            WHERE order_time >= DATE_SUB(NOW(), INTERVAL 1 MONTH)
            GROUP BY drink_name 
            ORDER BY count DESC 
            LIMIT 5
        """)
        
        top_drinks = [{'drink_name': row[0], 'count': row[1]} for row in result]
        
        return jsonify({
            'status': 'success',
            'data': top_drinks
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

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