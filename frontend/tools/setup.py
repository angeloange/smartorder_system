import os
import shutil
from datetime import datetime

def setup_project():
    """專案設定工具"""
    tools_dir = 'tools'
    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)
        
    # 移動工具腳本到 tools 目錄
    for script in ['merge_gitignore.py', 'restore_project.py']:
        if os.path.exists(script):
            shutil.move(script, os.path.join(tools_dir, script))

if __name__ == '__main__':
    setup_project()
