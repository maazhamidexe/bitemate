from flask_sqlalchemy import SQLAlchemy
from app import db

class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(1000), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20))
    address = db.Column(db.Text)


class Restaurant(db.Model):
    __tablename__ = 'restaurants'
    restaurant_id = db.Column(db.Integer, primary_key=True)
    restaurant_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255))
    total_rating = db.Column(db.Float, nullable=False)
    restaurant_image_path = db.Column(db.String(255))
    password = db.Column(db.String(100), nullable=False)
    is_open = db.Column(db.Boolean, default=True)
    category = db.Column(db.String(100))

class MenuItem(db.Model):
    __tablename__ = 'MenuItems'
    item_id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('Restaurants.restaurant_id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    item_image = db.Column(db.LargeBinary)
    is_available = db.Column(db.Boolean, default=True)

class Cart(db.Model):
    __tablename__ = 'Cart'
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('MenuItems.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    __tablename__ = 'Orders'
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('MenuItems.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())

class Review(db.Model):
    __tablename__ = 'Reviews'
    review_id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('Restaurants.restaurant_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review_text = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=db.func.current_timestamp())
