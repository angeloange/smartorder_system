from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    drink_name = db.Column(db.String(20), nullable=False)
    size = db.Column(db.Enum('大杯', '小杯'), nullable=False)
    ice_type = db.Column(db.Enum('iced', 'hot', 'room_temp'), nullable=False)
    sugar_type = db.Column(db.Enum('full', 'half', 'free'), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    order_time = db.Column(db.Time, nullable=False)
    weather_status = db.Column(db.Enum('sunny', 'cloudy', 'rainy', 'stormy'))
    temperature = db.Column(db.DECIMAL(4, 2))
    phone_number = db.Column(db.String(10))
    status = db.Column(db.String(20), default='pending')  # pending/processing/completed/cancelled

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'drink_name': self.drink_name,
            'size': self.size,
            'ice_type': self.ice_type,
            'sugar_type': self.sugar_type,
            'status': self.status,
            'created_at': f"{self.order_date} {self.order_time}"
        }

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    role = db.Column(db.String(20), default='staff')  # admin/staff
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    category = db.Column(db.String(50))  # tea/milk_tea/coffee
    description = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
