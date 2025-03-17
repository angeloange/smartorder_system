import os
import subprocess
from getpass import getpass

def setup_github():
    print("設定 GitHub 認證...")
    
    # 設定 Git 使用者資訊
    name = input("請輸入您的 GitHub 使用者名稱: ")
    email = input("請輸入您的 GitHub 電子郵件: ")
    
    subprocess.run(['git', 'config', 'user.name', name])
    subprocess.run(['git', 'config', 'user.email', email])
    
    # 重新設定遠端倉庫 URL
    token = getpass("請輸入您的 GitHub Personal Access Token: ")
    remote_url = f"https://{name}:{token}@github.com/angeloange/smartorder_system.git"
    
    subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url])
    print("\n認證設定完成！現在可以使用以下指令推送程式碼：")
    print("git push origin feature/integration")

if __name__ == "__main__":
    setup_github()
