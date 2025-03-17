import subprocess
import os

def check_git_status():
    """檢查 Git 狀態並列出目前所有分支狀態"""
    
    def run_cmd(cmd):
        """執行 Git 命令並返回結果"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"執行錯誤: {str(e)}"

    print("\n=== Git 狀態檢查 ===")
    
    # 1. 檢查當前分支
    current = run_cmd("git branch --show-current")
    print(f"\n當前分支: {current}")
    
    # 2. 列出所有本地分支
    local = run_cmd("git branch")
    print(f"\n本地分支:\n{local}")
    
    # 3. 列出所有遠端分支
    remote = run_cmd("git branch -r")
    print(f"\n遠端分支:\n{remote}")
    
    # 4. 檢查是否有未提交的變更
    status = run_cmd("git status --porcelain")
    if status:
        print(f"\n未提交的變更:\n{status}")
    else:
        print("\n工作目錄是乾淨的")

    print("\n=== 下一步建議 ===")
    print("1. 拉取最新更新:")
    print("   git fetch origin")
    print("2. 查看同事的分支:")
    print("   git checkout origin/[同事的分支名稱]")

if __name__ == "__main__":
    check_git_status()
