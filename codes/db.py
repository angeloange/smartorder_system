import os
import pymysql
from pymysql.cursors import DictCursor
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DBUser:
    host: str
    port: int
    user: str
    password: str
    database: str

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
        # 使用點運算符存取屬性
        self.host = config.host
        self.port = config.port
        self.user = config.user
        self.password = config.password
        self.database = config.database
        self.conn = None
        self.cursor = None

    def connect(self):
        """建立資料庫連接"""
        if not self.conn:
            try:
                self.conn = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    db=self.database,
                    charset='utf8mb4',
                    cursorclass=DictCursor
                )
                self.cursor = self.conn.cursor()
                print("資料庫連線成功")
            except Exception as e:
                print(f"資料庫連線失敗: {str(e)}")
                raise e

    def execute(self, query, data=None):
        try:
            if data:
                self.cursor.execute(query, data)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as e:
            print(f'execute錯誤: {e}')
            self.conn.rollback()
            return False

    def fetchall(self):
        try:
            return self.cursor.fetchall()
        except Exception as e:
            print(f'fetchall錯誤: {e}')
            return None

    def fetchone(self, query, params=None):
        """執行查詢並返回一筆結果"""
        try:
            if not self.conn or not self.cursor:
                self.connect()
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            print(f'fetchone錯誤: {e}')
            return None

    def close(self):
        """關閉資料庫連接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
        print('資料庫關閉連線')
        return True