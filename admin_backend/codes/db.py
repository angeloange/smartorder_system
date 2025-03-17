import mysql.connector
import os
from dotenv import load_dotenv
from mysql.connector import Error
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
    def __init__(self, account: DBUser):
        self.host = account.host
        self.port = account.port
        self.user = account.user
        self.password = account.password
        self.database = account.database
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.conn.is_connected():
                    print(f"資料庫: {self.database} 連線成功")
                    self.cursor = self.conn.cursor()
        except Error as e:
            print(f"資料庫錯誤: {e}")
            self.conn = None
            self.cursor = None

    def disconnect(self):
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            print('資料庫關閉連線')

    def execute(self, query: str, data: tuple = None):
        if self.conn and self.cursor:
            try:
                self.cursor.execute(query, data)
                self.conn.commit()
                return self.cursor.fetchall()  # 如果是查詢資料會返回結果
            except Exception as e:
                print(f"execute錯誤: {e}")
                return None
        else:
            print("資料庫尚未連線")
            return None

    def roll_back(self):
        self.conn.rollback()