import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """檢查環境設定"""
    # 載入環境變數
    env_path = Path(__file__).parent / '.env'
    print(f"\n檢查 .env 檔案:")
    print(f"- 路徑: {env_path}")
    print(f"- 是否存在: {env_path.exists()}")
    
    if env_path.exists():
        load_dotenv(env_path)
        print("- 已嘗試載入 .env 檔案")
    
    print("\n檢查 Python 路徑:")
    for path in sys.path:
        print(f"- {path}")
    
    print("\n檢查環境變數:")
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"- {var}: 已設定")
        else:
            print(f"- {var}: 未設定")
            all_set = False
    
    return all_set

if __name__ == '__main__':
    if check_environment():
        print("\n✅ 所有環境變數設定正確")
    else:
        print("\n❌ 部分環境變數未設定")