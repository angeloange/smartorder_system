import os
import pymysql
import sys
import threading
from dotenv import load_dotenv
from pathlib import Path

# 將專案根目錄和子目錄加入 Python 路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'admin_backend'))
sys.path.append(str(project_root / 'frontend'))



# 載入環境變數
def load_environment():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print("已載入環境變數")
    else:
        print("警告: .env 檔案不存在，請確保環境變數已透過其他方式設定")

# 測試資料庫連接
def test_db_connection():
    # 設置為 True 可跳過數據庫檢查
    BYPASS_DB_CHECK = True
    if BYPASS_DB_CHECK:
        print("跳過資料庫連接測試")
        return True

    try:
        print("🔍 測試數據庫連接...")
        # 檢查環境變數是否存在
        db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'db': os.getenv('DB_NAME'),
        }
        
        # 打印連接信息（移除密碼）
        db_info = db_config.copy()
        if 'password' in db_info:
            db_info['password'] = '******' if db_info['password'] else '(empty)'
        print(f"嘗試連接到: {db_info}")
        
        # 使用 pymysql 直接測試
        conn = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['db'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
        conn.close()
        print("資料庫連接測試成功")
        return True
    except Exception as e:
        print(f"資料庫連接測試失敗: {str(e)}")
        return False

# 獲取本機 IP 地址
def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "localhost"

# 啟動 Flask-SocketIO 伺服器
def run_server(socketio, app, port):
    print(f"服務啟動中: http://{get_local_ip()}:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 載入環境變數
    load_environment()
    
    # 定義必要的環境變數
    required_env_vars = [
        'DB_HOST', 'DB_PORT', 'DB_USER', 
        'DB_PASSWORD', 'DB_NAME', 'OPENAI_API_KEY'
    ]
    
    # 確認環境變數是否已載入
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"錯誤：缺少必要的環境變數：{', '.join(missing_vars)}")
        exit(1)

    # 測試資料庫連接
    if not test_db_connection():
        print("無法連接到資料庫，系統終止啟動")
        exit(1)

    # 獲取本機 IP 地址
    local_ip = get_local_ip()

    print("\n=== 智慧點餐系統啟動中 ===\n")
    print(f"前台系統運行於: http://{local_ip}:5002")
    print(f"後台系統運行於: http://{local_ip}:5003")
    
    # 推遲導入應用，避免循環導入問題
    from frontend.app import app as frontend_app, socketio as frontend_socketio
    from admin_backend.app import app as admin_app, socketio as admin_socketio
    
    # 確保前後台的 socketio 配置正確
    frontend_socketio.init_app(frontend_app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)
    admin_socketio.init_app(admin_app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)
    
    # 啟動前後台 SocketIO 伺服器（用 Thread 避免 Eventlet 衝突）
    frontend_thread = threading.Thread(target=run_server, args=(frontend_socketio, frontend_app, 5002))
    admin_thread = threading.Thread(target=run_server, args=(admin_socketio, admin_app, 5003))

    frontend_thread.start()
    admin_thread.start()

    try:
        frontend_thread.join()
        admin_thread.join()
    except KeyboardInterrupt:
        print("\n 正在關閉系統...")
        sys.exit(0)



# import os
# import sys
# from pathlib import Path
# import time
# import eventlet

# # 使用 eventlet 修補標準庫
# eventlet.monkey_patch()

# # 將專案根目錄和子目錄加入 Python 路徑
# project_root = Path(__file__).parent
# sys.path.append(str(project_root))
# sys.path.append(str(project_root / 'admin_backend'))
# sys.path.append(str(project_root / 'frontend'))

# from dotenv import load_dotenv
# import pymysql

# # 載入環境變數
# def load_environment():
#     dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
#     if os.path.exists(dotenv_path):
#         load_dotenv(dotenv_path)
#         print("已載入環境變數")
#     else:
#         print("警告: .env 檔案不存在，請確保環境變數已透過其他方式設定")

# # 測試資料庫連接
# def test_db_connection():
#     # 設置為 True 可跳過數據庫檢查
#     BYPASS_DB_CHECK = True
#     if BYPASS_DB_CHECK:
#         print("跳過資料庫連接測試")
#         return True
        
#     try:
#         print("測試數據庫連接...")
#         # 檢查環境變數是否存在
#         db_config = {
#             'host': os.getenv('DB_HOST'),
#             'port': int(os.getenv('DB_PORT', 3306)),
#             'user': os.getenv('DB_USER'),
#             'password': os.getenv('DB_PASSWORD'),
#             'db': os.getenv('DB_NAME'),
#         }
        
#         # 打印連接信息（移除密碼）
#         db_info = db_config.copy()
#         if 'password' in db_info:
#             db_info['password'] = '******' if db_info['password'] else '(empty)'
#         print(f"嘗試連接到: {db_info}")
        
#         # 使用 pymysql 直接測試
#         conn = pymysql.connect(
#             host=db_config['host'],
#             port=db_config['port'],
#             user=db_config['user'],
#             password=db_config['password'],
#             database=db_config['db'],
#             charset='utf8mb4',
#             cursorclass=pymysql.cursors.DictCursor
#         )
        
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT 1 as test")
#             result = cursor.fetchone()
            
#         conn.close()
#         print("資料庫連接測試成功")
#         return True
#     except Exception as e:
#         print(f"資料庫連接測試失敗: {str(e)}")
#         return False

# # 獲取本機 IP 地址
# def get_local_ip():
#     import socket
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(("8.8.8.8", 80))
#         local_ip = s.getsockname()[0]
#         s.close()
#         return local_ip
#     except Exception:
#         return "localhost"

# if __name__ == '__main__':
#     # 載入環境變數
#     load_environment()
    
#     # 定義必要的環境變數
#     required_env_vars = [
#         'DB_HOST', 'DB_PORT', 'DB_USER', 
#         'DB_PASSWORD', 'DB_NAME', 'OPENAI_API_KEY'
#     ]
    
#     # 確認環境變數是否已載入
#     missing_vars = [var for var in required_env_vars if not os.getenv(var)]
#     if missing_vars:
#         print(f"錯誤：缺少必要的環境變數：{', '.join(missing_vars)}")
#         exit(1)

#     # 測試資料庫連接
#     if not test_db_connection():
#         print("無法連接到資料庫，系統終止啟動")
#         exit(1)

#     # 獲取本機 IP 地址
#     local_ip = get_local_ip()

#     print("\n=== 智慧點餐系統啟動中 ===")
#     print(f"前台系統將運行於: http://{local_ip}:5002")
#     print(f"後台系統將運行於: http://{local_ip}:5003")
    
#     # 推遲導入應用，避免循環導入問題
#     from frontend.app import app as frontend_app, socketio as frontend_socketio
#     from admin_backend.app import app as admin_app, socketio as admin_socketio
    
#     # 確保前後台的 socketio 配置正確
#     frontend_socketio.init_app(frontend_app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)
#     admin_socketio.init_app(admin_app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)
    
#     # 使用 eventlet 分別啟動前台和後台
#     print("正在啟動前台系統...")
#     frontend_server = eventlet.spawn(frontend_socketio.run, 
#                                     frontend_app, 
#                                     host='0.0.0.0', 
#                                     port=5002, 
#                                     debug=True,
#                                     use_reloader=False)
    
#     print("正在啟動後台系統...")
#     admin_server = eventlet.spawn(admin_socketio.run, 
#                                  admin_app, 
#                                  host='0.0.0.0', 
#                                  port=5003, 
#                                  debug=True, 
#                                  use_reloader=False)
    
#     try:
#         # 等待兩個服務器
#         frontend_server.wait()
#         admin_server.wait()
#     except KeyboardInterrupt:
#         print("\n正在關閉系統...")
#         print("系統已關閉")
#         sys.exit(0)