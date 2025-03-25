from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
import enum
import pytz

db = SQLAlchemy()

class OrderStatus(enum.Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

def get_tw_time():
    return datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Taipei'))

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drink_name = db.Column(db.String(20), nullable=False)
    size = db.Column(db.Enum('大杯', '小杯'), nullable=False, default='小杯')
    ice_type = db.Column(db.Enum('iced', 'less', 'light', 'no_ice', 'hot', 'room'), 
                        nullable=False, 
                        default='room')    
    sugar_type = db.Column(db.Enum('full', 'seventy', 'half', 'light', 'free'), 
                          nullable=False, 
                          default='half')    
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    order_time = db.Column(db.Time, nullable=False, default=datetime.utcnow().time)
    weather_status = db.Column(db.Enum('sunny', 'cloudy', 'rainy', 'stormy'), nullable=False, default='cloudy')
    temperature = db.Column(db.DECIMAL(4, 2), nullable=False, default=20.00)
    phone_number = db.Column(db.String(10))
    status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=get_tw_time, onupdate=get_tw_time)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    order_number = db.Column(db.String(20))


    @property
    def sugar_type_display(self):
        sugar_map = {
            'full': '全糖',
            'seventy': '七分糖',
            'half': '半糖',
            'light': '微糖',
            'free': '無糖'
        }
        return sugar_map.get(self.sugar_type, self.sugar_type)
    
    @property
    def ice_type_display(self):
        ice_map = {
            'iced': '正常冰',
            'less': '少冰',
            'light': '微冰',
            'no_ice': '去冰',
            'hot': '熱飲',
            'room': '常溫'
        }
        return ice_map.get(self.ice_type, str(self.ice_type))
    @property
    def status_display(self):
        status_map = {
            OrderStatus.PENDING: '待處理',
            OrderStatus.PROCESSING: '製作中',
            OrderStatus.COMPLETED: '已完成',
            OrderStatus.CANCELLED: '已取消'
        }
        return status_map.get(self.status, str(self.status))

    @property
    def status_color(self):
        color_map = {
            OrderStatus.PENDING: 'warning',
            OrderStatus.PROCESSING: 'info',
            OrderStatus.COMPLETED: 'success',
            OrderStatus.CANCELLED: 'danger'
        }
        return color_map.get(self.status, 'secondary')

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'drink_name': self.drink_name,
            'size': self.size,
            'ice_type': self.ice_type,
            'sugar_type': self.sugar_type,
            'status': self.status.value,
            'status_display': self.status_display,
            'status_color': self.status_color,
            'order_date': self.order_date.strftime('%Y-%m-%d'),
            'order_time': self.order_time.strftime('%H:%M:%S'),
            'weather_status': self.weather_status,
            'temperature': float(self.temperature) if self.temperature else None,
            'phone_number': self.phone_number,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    role = db.Column(db.Enum('admin', 'staff'), nullable=False, default='staff')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'image_url': self.image_url,
            'is_available': self.is_available,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }



class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_setting(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_setting(cls, key, value):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
