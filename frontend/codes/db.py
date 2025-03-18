import pymysql
from pymysql.cursors import DictCursor
import os
from dotenv import load_dotenv
from .models import DBUser

load_dotenv()

def dbconfig() -> DBUser:
    return DBUser(
         host=os.getenv("DB_HOST"),
         port=int(os.getenv("DB_PORT")),
         user=os.getenv("DB_USER"),
         password=os.getenv("DB_PASSWORD"),
         database=os.getenv("DB_NAME")
         )

class DB:
    def __init__(self, config: DBUser):
        self.config = config
        self.conn = None
        self.cursor = None
        # 初始化時就建立連接
        self.connect()

    def connect(self):
        """建立資料庫連接"""
        try:
            if not self.conn or not self.cursor:
                self.conn = pymysql.connect(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.user,
                    password=self.config.password,
                    db=self.config.database,
                    charset='utf8mb4',
                    cursorclass=DictCursor
                )
                self.cursor = self.conn.cursor()
                print("資料庫連線成功")
                return True
            return True
        except Exception as e:
            print(f"資料庫連線失敗: {str(e)}")
            return False

    def fetch_all(self, query, params=None):
        try:
            self.connect()
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def execute(self, query, params=None):
        """執行 SQL 查詢"""
        try:
            if not self.conn or not self.cursor:
                if not self.connect():
                    raise Exception("無法建立資料庫連接")
            
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"執行查詢錯誤: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False