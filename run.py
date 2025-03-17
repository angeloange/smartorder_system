import os
import sys
from pathlib import Path

# 將專案根目錄和子目錄加入 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'admin_backend'))
sys.path.append(str(project_root / 'frontend'))

from dotenv import load_dotenv
from frontend.app import app as frontend_app
from admin_backend.app import app as admin_app
from dotenv import load_dotenv
from frontend.app import app as frontend_app
from admin_backend.app import app as admin_app
from threading import Thread
from werkzeug.serving import run_simple
import time

# 載入環境變數
load_dotenv()

def test_db_connection():
    """測試資料庫連接"""
    try:
        from codes.db import DB, dbconfig
        db = DB(dbconfig())
        db.connect()
        print("資料庫連接測試成功")
        return True
    except Exception as e:
        print(f"資料庫連接測試失敗: {str(e)}")
        return False

def run_frontend():
    try:
        print("正在啟動前台系統...")
        run_simple('localhost', 5002, frontend_app, use_debugger=True, use_reloader=False)
    except Exception as e:
        print(f"前台系統啟動失敗: {str(e)}")

def run_backend():
    try:
        print("正在啟動後台系統...")
        run_simple('localhost', 5003, admin_app, use_debugger=True, use_reloader=False)
    except Exception as e:
        print(f"後台系統啟動失敗: {str(e)}")


def load_environment():
    """載入環境變數"""
    env_path = Path(__file__).parent / '.env'
    print(f"\n正在載入環境變數檔案: {env_path}")
    
    if not env_path.exists():
        print(f"錯誤：找不到 .env 檔案")
        return False
        
    load_dotenv(env_path)
    print("環境變數檔案載入完成")
    return True


if __name__ == '__main__':
    # 載入環境變數
    load_environment()
    
    # 確認環境變數是否已載入
    required_env_vars = [
        'DB_HOST', 'DB_PORT', 'DB_USER', 
        'DB_PASSWORD', 'DB_NAME', 'OPENAI_API_KEY'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"錯誤：缺少必要的環境變數：{', '.join(missing_vars)}")
        exit(1)

    # 測試資料庫連接
    if not test_db_connection():
        print("無法連接到資料庫，系統終止啟動")
        exit(1)

    print("\n=== 智慧點餐系統啟動中 ===")
    print(f"前台系統將運行於: http://localhost:5002")
    print(f"後台系統將運行於: http://localhost:5003")
    
    # 建立前後台的執行緒
    frontend_thread = Thread(target=run_frontend)
    backend_thread = Thread(target=run_backend)

    # 設定為 daemon 執行緒，讓主程式結束時自動結束
    frontend_thread.daemon = True
    backend_thread.daemon = True

    # 啟動執行緒
    frontend_thread.start()
    backend_thread.start()

    try:
        # 保持主程式運行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在關閉系統...")
        print("系統已關閉")