from app import app, db
from models import Admin, Product
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # 建立資料表
        db.create_all()
        
        # 建立預設管理員
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                name='系統管理員',
                email='admin@example.com',
                role='admin'
            )
            db.session.add(admin)
            
        # 建立一些測試產品
        sample_products = [
            {'name': '綠茶', 'price': 30, 'category': 'tea'},
            {'name': '紅茶', 'price': 30, 'category': 'tea'},
            {'name': '奶茶', 'price': 45, 'category': 'milk_tea'},
        ]
        
        for product in sample_products:
            if not Product.query.filter_by(name=product['name']).first():
                new_product = Product(**product)
                db.session.add(new_product)
        
        db.session.commit()

if __name__ == '__main__':
    init_database()
