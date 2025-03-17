import pymysql
from dotenv import load_dotenv
import os

def check_database_structure():
    """檢查現有資料庫結構"""
    load_dotenv()
    
    # 連接資料庫
    connection = pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME')
    )
    
    try:
        with connection.cursor() as cursor:
            # 獲取所有表格
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print("\n=== 資料庫結構分析 ===")
            
            # 檢查每個表格的結構
            for table in tables:
                table_name = table[0]
                print(f"\n資料表：{table_name}")
                
                # 獲取表格結構
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                print("欄位結構：")
                for column in columns:
                    print(f"- {column[0]}: {column[1]}")
                
                # 獲取外鍵關係
                cursor.execute(f"""
                    SELECT 
                        COLUMN_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME 
                    FROM 
                        INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE 
                        TABLE_NAME = '{table_name}' 
                        AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                foreign_keys = cursor.fetchall()
                
                if foreign_keys:
                    print("\n外鍵關係：")
                    for fk in foreign_keys:
                        print(f"- {fk[0]} -> {fk[1]}({fk[2]})")
    
    finally:
        connection.close()

if __name__ == "__main__":
    check_database_structure()
