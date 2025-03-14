import os

class Config:
    # 取得專案根目錄
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # 使用 SQLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'voice_order.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key'