from frontend.app import app, db
from sqlalchemy import text

def verify_connection():
    with app.app_context():
        try:
            # 強制建立新連線
            db.engine.dispose()
            
            # 測試連線
            result = db.session.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            print(f"已連線到：{db_name}")
            
            # 檢查資料表
            result = db.session.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print("\n可用資料表：")
            for table in tables:
                print(f"- {table[0]}")
                
        except Exception as e:
            print(f"錯誤：{str(e)}")
            
if __name__ == "__main__":
    verify_connection()