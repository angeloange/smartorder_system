from app import app, db
from models import Admin, Order, Product, OrderStatus
from datetime import datetime, timedelta
import random

def create_sample_data():
    with app.app_context():
        # 建立測試產品
        products = [
            Product(
                name='珍珠奶茶',
                price=60,
                category='milk_tea',
                description='招牌珍珠奶茶，使用進口奶茶及特製珍珠',
                is_available=True
            ),
            Product(
                name='四季春茶',
                price=45,
                category='tea',
                description='清爽四季春茶，茶香濃郁',
                is_available=True
            ),
            Product(
                name='美式咖啡',
                price=50,
                category='coffee',
                description='100%阿拉比卡咖啡豆',
                is_available=True
            )
        ]
        
        for product in products:
            db.session.add(product)
        
        # 建立測試訂單
        statuses = [status for status in OrderStatus]
        ice_types = ['hot', 'iced', 'room_temp']
        sugar_types = ['full', 'half', 'free']
        
        for i in range(20):
            order_date = datetime.now() - timedelta(days=random.randint(0, 7))
            product = random.choice(products)
            
            order = Order(
                drink_name=product.name,
                size=random.choice(['大杯', '小杯']),
                ice_type=random.choice(ice_types),
                sugar_type=random.choice(sugar_types),
                status=random.choice(statuses),
                order_date=order_date.date(),
                order_time=order_date.time(),
                weather_status=random.choice(['sunny', 'cloudy', 'rainy']),
                temperature=round(random.uniform(20.0, 30.0), 1),
                phone_number=f'09{random.randint(10000000, 99999999)}'
            )
            db.session.add(order)
        
        db.session.commit()
        print('已建立測試資料')

if __name__ == '__main__':
    create_sample_data()