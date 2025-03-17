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

    def connect(self):
        if not self.conn:
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

    def fetch_all(self, query, params=None):
        try:
            self.connect()
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def execute(self, query, params=None):
        try:
            self.connect()
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return False