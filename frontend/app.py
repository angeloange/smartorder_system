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

if __name__ == '__main__':
    app.run(debug=True, port=5005)