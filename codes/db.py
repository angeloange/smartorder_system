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
    def __init__(self, config):
        self.host = config['host']
        self.user = config['user']
        self.password = config['password']
        self.database = config['db']
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.conn.cursor(dictionary=True)
            print(f'資料庫: {self.database} 連線成功')
            return True
        except mysql.connector.Error as err:
            print(f'資料庫連線失敗: {err}')
            return False

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

    def fetchone(self):
        try:
            return self.cursor.fetchone()
        except Exception as e:
            print(f'fetchone錯誤: {e}')
            return None

    def disconnect(self):
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            
            if self.conn:
                self.conn.close()
                self.conn = None
                
            print('資料庫關閉連線')
            return True
        except Exception as e:
            print(f'資料庫關閉連線失敗: {e}')
            return False