import subprocess

def stash_and_switch():
    """暫存更改並切換分支"""
    print("=== 執行暫存操作 ===")
    
    # 1. 暫存當前更改
    subprocess.run(['git', 'stash', 'save', '暫存 .gitignore 更改'])
    print("已暫存更改")
    
    # 2. 切換分支
    subprocess.run(['git', 'checkout', 'origin/dev'])
    print("已切換到 dev 分支")
    
    print("\n如果要恢復暫存的更改：")
    print("git stash pop")

if __name__ == "__main__":
    stash_and_switch()
