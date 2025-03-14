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

app = Flask(__name__)
app.config.from_object(Config)

# 重新初始化資料庫連線
db = SQLAlchemy()
db.init_app(app)

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

class VoiceOrder(db.Model):
    __tablename__ = 'orders'  # 改用正確的資料表名稱
    
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drink_name = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Enum(Size), nullable=False, default=Size.SMALL)
    ice_type = db.Column(db.Enum(IceType), nullable=False, default=IceType.ROOM_TEMP)
    sugar_type = db.Column(db.Enum(SugarType), nullable=False, default=SugarType.HALF)
    order_date = db.Column(db.Date, default=datetime.utcnow().date)
    order_time = db.Column(db.Time, default=datetime.utcnow().time)
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
        print(f"收到訂單資料：{data}")
        
        # 處理每個飲料訂單
        for order_item in data['order_details']:
            # 確保所有欄位都有正確的格式
            ice_type = order_item['ice'].upper()
            sugar_type = order_item['sugar'].upper()
            size = order_item.get('size', '小杯')
            
            # 建立訂單
            order = VoiceOrder(
                drink_name=order_item['drink_name'],
                size=Size.LARGE if size == '大杯' else Size.SMALL,
                ice_type=IceType[ice_type] if ice_type in IceType.__members__ else IceType.ROOM_TEMP,
                sugar_type=SugarType[sugar_type] if sugar_type in SugarType.__members__ else SugarType.HALF,
                order_date=datetime.now().date(),
                order_time=datetime.now().time(),
                weather_status=WeatherStatus.CLOUDY,
                temperature=20.00,
                phone_number=data.get('phone_number')
            )
            db.session.add(order)
            
        db.session.commit()
        print("訂單已儲存到資料庫")
        
        return jsonify({
            'status': 'success',
            'message': '訂單已確認並儲存'
        })
        
    except Exception as e:
        print(f"儲存訂單時發生錯誤：{str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
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

if __name__ == '__main__':
    app.run(debug=True, port=5002)