import os
import shutil

def create_structure():
    # 建立基礎目錄結構
    directories = [
        'frontend/templates',
        'frontend/static/js',
        'frontend/static/css',
        'admin_backend/templates',
        'admin_backend/static/js',
        'admin_backend/static/css',
        'shared/models',
        'shared/utils'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"建立目錄: {directory}")
    
    # 移動檔案到對應位置
    file_moves = [
        # 前端檔案
        ('littleproject/app.py', 'frontend/app.py'),
        ('littleproject/templates/*', 'frontend/templates/'),
        ('littleproject/static/*', 'frontend/static/'),
        
        # 後端檔案
        ('admin_backend/app.py', 'admin_backend/app.py'),
        
        # 共用檔案
        ('virtual_assistant', 'shared/virtual_assistant'),
    ]
    
    for src, dest in file_moves:
        try:
            if os.path.exists(src):
                if src.endswith('/*'):
                    src_dir = src[:-2]
                    for item in os.listdir(src_dir):
                        s = os.path.join(src_dir, item)
                        d = os.path.join(dest, item)
                        if os.path.isfile(s):
                            shutil.copy2(s, d)
                        elif os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    if os.path.isfile(src):
                        shutil.copy2(src, dest)
                    elif os.path.isdir(src):
                        shutil.copytree(src, dest, dirs_exist_ok=True)
                print(f"移動: {src} -> {dest}")
        except Exception as e:
            print(f"移動 {src} 時發生錯誤: {e}")

if __name__ == '__main__':
    create_structure()
