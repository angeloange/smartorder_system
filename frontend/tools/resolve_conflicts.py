import os
import subprocess

def resolve_conflicts():
    """衝突解決工具"""
    print("\n=== 衝突檔案處理指南 ===")
    
    # 1. 顯示衝突檔案
    status = subprocess.getoutput('git status')
    print("衝突檔案:")
    print("1. .gitignore")
    print("2. app.py")
    
    print("\n解決步驟:")
    print("1. 正在檢查 .gitignore...")
    
    # 清理 .gitignore 的衝突標記
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*.so
.Python
*.pyc

# 環境設定
.env
.env.*
venv/
.venv/

# IDE
.vscode/
.idea/

# 專案特定
temp_audio/
instance/
logs/
test*
tempCodeRunnerFile.py

# 系統檔案
.DS_Store
    """
    
    # 寫入清理後的 .gitignore
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content.strip())
    
    print("\n已更新 .gitignore")
    print("\n請執行:")
    print("1. 檢查更新後的 .gitignore 內容")
    print("2. 檢查 app.py 的衝突")
    print("3. 執行: git add .gitignore")
    print("4. 執行: git add app.py")
    print("5. 執行: git commit -m '解決合併衝突'")

if __name__ == "__main__":
    resolve_conflicts()
