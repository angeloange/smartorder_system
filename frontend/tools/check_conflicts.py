import subprocess
import sys

def check_app_conflicts():
    """檢查 app.py 的衝突內容"""
    try:
        # 獲取 app.py 的衝突內容
        result = subprocess.run(['git', 'diff', 'app.py'], 
                             capture_output=True, 
                             text=True)
        
        print("\n=== app.py 衝突內容分析 ===")
        print("請檢查以下區域：")
        
        # 分析衝突內容
        content = result.stdout
        if '<<<<<<< HEAD' in content:
            print("\n1. 當前分支的程式碼 (HEAD):")
            print("   從 <<<<<<< HEAD 到 =======")
            print("\n2. dev 分支的程式碼:")
            print("   從 ======= 到 >>>>>>> origin/dev")
            
            print("\n建議：")
            print("1. 打開 app.py")
            print("2. 搜尋 <<<<<<< 標記")
            print("3. 決定要保留的程式碼")
            print("4. 移除衝突標記")
            
            # 顯示合併指令
            print("\n完成後執行：")
            print("git add app.py")
            print("git commit -m '解決 app.py 的合併衝突'")
        
    except Exception as e:
        print(f"檢查失敗: {str(e)}")

if __name__ == "__main__":
    check_app_conflicts()
