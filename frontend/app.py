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
from .order_analyzer import OrderAnalyzer

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
    """生成新的訂單號碼（MMDDA1-MMDDZ9）"""
    today = datetime.now().strftime('%m%d')
    last_number = get_last_order_number(db)
    
    # 基本訂單號碼
    if not last_number:
        base_number = f'{today}A1'  # 當天第一筆訂單
    else:
        # 從完整訂單號碼中提取字母和數字
        if '-' in last_number:
            base_last = last_number.split('-')[0]
        else:
            base_last = last_number
            
        letter = base_last[-2]  # 倒數第二個字符（字母）
        number = int(base_last[-1])  # 最後一個字符（數字）
        
        if number < 9:
            base_number = f'{today}{letter}{number + 1}'
        else:
            next_letter = chr(ord(letter) + 1) if letter != 'Z' else 'A'
            base_number = f'{today}{next_letter}1'
    
    # 生成所有訂單號碼
    order_numbers = []
    for i in range(count):
        if i == 0:
            order_numbers.append(base_number)
        else:
            # 使用連字號+序號，避免衝突
            order_numbers.append(f"{base_number}-{i+1}")
    
    return order_numbers

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    try:
        data = request.get_json()
        order_details = data.get('order_details', [])
        
        # 展開訂單項目，處理相同品項多杯的情況
        expanded_orders = []
        for order in order_details:
            # 獲取數量，預設為1
            quantity = order.get('quantity', 1)
            
            # 根據數量複製訂單項目
            for i in range(quantity):
                # 創建新的訂單項目，但不包含 quantity
                order_item = {k: v for k, v in order.items() if k != 'quantity'}
                expanded_orders.append(order_item)
        
        # 生成足夠數量的訂單號碼
        order_numbers = generate_order_number(db, len(expanded_orders))
        if not order_numbers:
            raise Exception("無法生成訂單號碼")
        
        # 取得當前時間和天氣資訊
        order_date, order_time = get_now_time()
        
        success_count = 0
        
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
                    order['drink_name'], order['size'],
                    order['ice'], order['sugar'],
                    order_date, order_time,
                    'sunny', 25.0,
                    'pending', order_numbers[i]
                )
                
                print(f"準備插入訂單，值為: {values}")
                if db.execute(query, values):
                    success_count += 1
                else:
                    print(f"插入訂單失敗: {values}")
            except Exception as e:
                print(f"插入單筆訂單時發生錯誤: {str(e)}")
        
        if success_count == 0:
            raise Exception("所有訂單儲存失敗")
            
        return jsonify({
            'status': 'success',
            'message': f'成功建立 {success_count}/{len(expanded_orders)} 筆訂單',
            'order_number': order_numbers[0][-2:]  # 只返回第一杯飲料號碼的最後兩位
        })

    except Exception as e:
        print(f"儲存訂單時發生錯誤: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '訂單處理失敗'
        })


if __name__ == '__main__':
    app.run(debug=True)