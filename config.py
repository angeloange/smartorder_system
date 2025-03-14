import os

class Config:
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # 資料庫設定
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'voice_order.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 從系統環境變數讀取 API Key
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # 檢查 API Key 是否存在
    @classmethod
    def validate_config(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError('找不到 OPENAI_API_KEY 環境變數')