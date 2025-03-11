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
load_dotenv()

app = Flask(__name__)
# MySQL 資料庫連接設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://voice_order_user:24999441@localhost/voice_order_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config['UPLOAD_FOLDER'] = 'temp_audio'

# 確保臨時音訊檔案夾存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class VoiceOrder(db.Model):
    __tablename__ = 'voice_orders'  # 對應到 MySQL 的資料表名稱
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自動遞增的 ID
    speech_text = db.Column(db.Text, nullable=False)  # 語音辨識文字
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())  # 建立時間

@app.route('/')
def index():
    return render_template('index.html')  # 只需要提供檔案名稱

analyzer = OrderAnalyzer()

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    try:
        # 模擬錄音輸入
        text = "我要一杯大杯冰綠茶，全糖微冰，兩杯珍珠奶茶半糖去冰，再一杯溫的紅茶，半糖，兩杯青茶，一杯無糖微冰，一杯全糖去冰"
        print(f"處理訂單文字: {text}")  # 新增除錯訊息
        
        # 分析訂單
        order_details = analyzer.analyze_order(text)
        print(f"分析結果: {order_details}")  # 新增除錯訊息

        return jsonify({
            'status': 'success',
            'speech_text': text,
            'order_details': order_details
        })

    except Exception as e:
        print(f"發生錯誤: {str(e)}")  # 新增除錯訊息
        return jsonify({
            'status': 'error',
            'message': f'處理時發生錯誤: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True)