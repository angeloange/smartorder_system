import os
import subprocess
import urllib.parse
from getpass import getpass

def update_credentials():
    print("更新 GitHub 認證設定...")
    
    # 移除舊的認證資訊
    subprocess.run(['git', 'config', '--global', '--unset-all', 'credential.helper'])
    
    # 設定新的認證資訊
    username = 'angeloange'
    email = input("請輸入您的 GitHub 電子郵件: ")
    token = getpass("請輸入您的 GitHub Personal Access Token: ")
    
    # URL encode the token to handle special characters
    encoded_token = urllib.parse.quote(token, safe='')
    
    # 更新 Git 配置
    subprocess.run(['git', 'config', '--global', 'user.name', username])
    subprocess.run(['git', 'config', '--global', 'user.email', email])
    
    # 更新遠端倉庫 URL (使用編碼後的 token)
    remote_url = f"https://{username}:{encoded_token}@github.com/angeloange/smartorder_system.git"
    subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url])
    
    print("\n認證已更新！")
    print("請執行:")
    print("1. git push origin feature/integration")

if __name__ == "__main__":
    update_credentials()
