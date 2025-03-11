from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy  # 新增這行
from order_analyzer import OrderAnalyzer
import json

app = Flask(__name__)# 新增資料庫設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://voice_order_user:24999441@localhost/voice_order_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 新增資料模型
class VoiceOrder(db.Model):
    __tablename__ = 'voice_orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drink_name = db.Column(db.String(100), nullable=False)
    ice_type = db.Column(db.String(50), nullable=False)
    suger_type = db.Column(db.String(50), nullable=False)
    order_data = db.Column(db.Text)
    order_time = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    weather_status = db.Column(db.String(100))
    weather_temperature = db.Column(db.DECIMAL(4,1))
    phone_number = db.Column(db.String(20))

analyzer = OrderAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    try:
        # 模擬錄音輸入
        text = "我要一杯大杯冰綠茶，全糖微冰"
        order_details = analyzer.analyze_order(text)
        
        return jsonify({
            'status': 'success',
            'speech_text': text,
            'order_details': order_details
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    try:
        data = request.json
        print(f"收到訂單資料：{data}")  # 除錯訊息
        
        # 處理每一個飲料訂單
        for order_item in data['order_details']:
            new_order = VoiceOrder(
                drink_name=order_item['drink_name'],
                ice_type=order_item['ice'],
                suger_type=order_item['sugar'],
                order_data=json.dumps(data['order_details'])
            )
            db.session.add(new_order)
        
        db.session.commit()
        print("訂單已儲存到資料庫")  # 除錯訊息

        return jsonify({
            'status': 'success',
            'message': '好的，尊貴的客人請稍候，正在為您製作飲品'
        })

    except Exception as e:
        print(f"儲存訂單時發生錯誤：{str(e)}")  # 除錯訊息
        return jsonify({
            'status': 'error',
            'message': f'儲存訂單時發生錯誤: {str(e)}'
        })


if __name__ == '__main__':
    app.run(debug=True,port='5002')