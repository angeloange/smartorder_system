from app import app, db
from models import Admin
from sqlalchemy import text

def init_db():
    with app.app_context():
        # 先關閉外鍵檢查
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=0;'))
        
        # 刪除所有現有的資料表
        db.drop_all()
        
        # 建立新的資料表
        db.create_all()
        
        # 重新開啟外鍵檢查
        db.session.execute(text('SET FOREIGN_KEY_CHECKS=1;'))
        
        # 建立預設管理員帳號
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                name='系統管理員',
                email='admin@example.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('已建立預設管理員帳號')

if __name__ == '__main__':
    init_db()
