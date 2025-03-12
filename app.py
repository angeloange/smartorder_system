from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import speech_recognition as sr
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import soundfile as sf
import io
import numpy as np
from pydub import AudioSegment
from order_analyzer import OrderAnalyzer
import json  # 新增這行
from sqlalchemy import func, extract
from datetime import datetime
load_dotenv()

app = Flask(__name__)
# MySQL 資料庫連接設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://voice_order_user:24999441@localhost/voice_order_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config['UPLOAD_FOLDER'] = 'temp_audio'

# 確保臨時音訊檔案夾存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 修改 VoiceOrder 模型
class VoiceOrder(db.Model):
    __tablename__ = 'voice_orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drink_name = db.Column(db.String(100), nullable=False)
    ice_type = db.Column(db.String(50), nullable=False)
    suger_type = db.Column(db.String(50), nullable=False)
    order_data = db.Column(db.Text)  # 保持這個欄位
    order_time = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    weather_status = db.Column(db.String(100))
    weather_temperature = db.Column(db.DECIMAL(4,1))
    phone_number = db.Column(db.String(20))
    # 移除 speech_text 欄位，因為我們使用 order_data

@app.route('/')
def menu():
    return render_template('index.html')

analyzer = OrderAnalyzer()

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    try:
        if 'audio' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未收到音訊檔案'
            }), 400

        audio_file = request.files['audio']
        
        # 確保臨時資料夾存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # 處理音訊檔案
        temp_webm = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.webm')
        audio_file.save(temp_webm)

        # 轉換為 WAV 格式
        temp_wav = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.wav')
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

        return jsonify({
            'status': 'success',
            'speech_text': text,
            'order_details': order_details
        })

    except Exception as e:
        print(f"錯誤: {str(e)}")  # 除錯用
        return jsonify({
            'status': 'error',
            'message': f'處理時發生錯誤: {str(e)}'
        })

# 修改 confirm_order 函數
@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    try:
        data = request.json
        order_details = data.get('order_details', [])
        speech_text = data.get('speech_text', '')
        
        for order in order_details:
            for _ in range(order.get('quantity', 1)):
                new_order = VoiceOrder(
                    drink_name=order.get('drink_name'),
                    ice_type=order.get('ice'),      
                    suger_type=order.get('sugar'),  
                    order_data=speech_text,  # 這裡改用 order_data 存儲語音文字
                )
                db.session.add(new_order)
                print(f"新增訂單: {order}")
        
        db.session.commit()
        print(f"已建立 {sum(order['quantity'] for order in order_details)} 筆訂單記錄")

        return jsonify({
            'status': 'success',
            'message': '好的，尊貴的客人請稍候，正在為您製作飲品'
        })

    except Exception as e:
        db.session.rollback()
        print(f"儲存訂單時發生錯誤：{str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                'status': 'error',
                'message': '未收到訂單內容'
            }), 400

        # 分析訂單
        order_details = analyzer.analyze_order(text)

        return jsonify({
            'status': 'success',
            'order_details': order_details
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/monthly_top_drinks', methods=['GET'])
def get_monthly_top_drinks():
    try:
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # 查詢當月熱銷飲料
        top_drinks = db.session.query(
            VoiceOrder.drink_name,
            func.count(VoiceOrder.drink_name).label('count')
        ).filter(
            extract('month', VoiceOrder.order_time) == current_month,
            extract('year', VoiceOrder.order_time) == current_year
        ).group_by(
            VoiceOrder.drink_name
        ).order_by(
            func.count(VoiceOrder.drink_name).desc()
        ).limit(3).all()
        
        # 格式化結果
        result = [
            {
                'drink_name': drink_name,
                'count': count
            } for drink_name, count in top_drinks
        ]
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        print(f"查詢熱銷飲料時發生錯誤：{str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True,port="5002")