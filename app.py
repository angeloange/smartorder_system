from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from order_analyzer import OrderAnalyzer
import json
import os
import datetime
from datetime import datetime
app = Flask(__name__)

# 資料庫設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://voice_order_user:24999441@localhost/voice_order_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
analyzer = OrderAnalyzer()

class VoiceOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drink_name = db.Column(db.String(100), nullable=False)
    ice_type = db.Column(db.String(20), nullable=False)
    suger_type = db.Column(db.String(20), nullable=False)
    order_data = db.Column(db.Text, nullable=False)
    order_time = db.Column(db.DateTime, default=datetime.utcnow)

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
        print(f"收到訂單資料：{data}")
        
        # 處理每個飲料訂單
        for order_item in data['order_details']:
            new_order = VoiceOrder(
                drink_name=order_item['drink_name'],
                ice_type=order_item['ice'],
                suger_type=order_item['sugar'],
                order_data=json.dumps(data['order_details'])
            )
            db.session.add(new_order)
        
        db.session.commit()
        print("訂單已儲存到資料庫")

        return jsonify({
            'status': 'success',
            'message': '訂單已確認並儲存'
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
            FROM voice_orders 
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