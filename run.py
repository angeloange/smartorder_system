from frontend.app import app as frontend_app
from admin_backend.app import app as admin_app
from werkzeug.serving import run_simple

if __name__ == '__main__':
    # 前端應用運行在 5002 埠
    run_simple('localhost', 5002, frontend_app, use_debugger=True, use_reloader=True)
    
    # 後端管理介面運行在 5003 埠
    run_simple('localhost', 5003, admin_app, use_debugger=True, use_reloader=True)
