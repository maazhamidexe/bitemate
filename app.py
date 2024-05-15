from flask import Flask, render_template, request, url_for, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import paypalrestsdk
import os
from werkzeug.utils import secure_filename
from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from flask import abort

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:pgadmin@localhost:5432/bitemate"
app.config["SECRET_KEY"] = "your_secret_key"  # Make sure to use a secure, random secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(1000), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20))
    address = db.Column(db.Text)

    def is_active(self):
        # All users are active in this case
        return True
    
    def get_id(self):
        # Return the user's ID
        return str(self.user_id)
    
    def is_authenticated(self):
        # All users are authenticated in this case
        return True

    def is_anonymous(self):
        # All users are not anonymous in this case
        return False

    # Add error handling for invalid data
    def validate(self):
        if not self.username:
            raise ValueError("Username is required.")
        if not self.password:
            raise ValueError("Password is required.")
        if not self.full_name:
            raise ValueError("Full name is required.")


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

    def is_active(self):
        # All users are active in this case
        return True
    
    def get_id(self):
        # Return the user's ID
        return str(self.restaurant_id)
    
    def is_authenticated(self):
        # All users are authenticated in this case
        return True

    def is_anonymous(self):
        # All users are not anonymous in this case
        return False

    # Add error handling for invalid data
    def validate(self):
        if not self.username:
            raise ValueError("Username is required.")
        if not self.password:
            raise ValueError("Password is required.")
        if not self.full_name:
            raise ValueError("Full name is required.")


class MenuItem(db.Model):
    __tablename__ = 'menuitems'
    item_id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.restaurant_id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    item_image = db.Column(db.String(100))
    is_available = db.Column(db.Boolean, default=True)


class Cart(db.Model):
    __tablename__ = 'cart'
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('menuitems.item_id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.restaurant_id'), nullable=False)  # Added restaurant_id column
    quantity = db.Column(db.Integer, nullable=False)
    item_image = db.Column(db.String(255))

class Order(db.Model):
    __tablename__ = 'orders'

    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('menuitems.item_id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.restaurant_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.DECIMAL(8, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    order_date = db.Column(db.TIMESTAMP, default=db.func.current_timestamp(), nullable=False)

    # Define relationships
    user = db.relationship("Users")
    item = db.relationship("MenuItem")
    restaurant = db.relationship("Restaurant")

class Review(db.Model):
    __tablename__ = 'reviews'

    review_id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.restaurant_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review_text = db.Column(db.Text)
    review_date = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    
    # Define relationships
    user = db.relationship("Users", backref=db.backref("reviews", cascade="all, delete-orphan"))

    def calculate_average_rating(self):
        # Calculate the average rating for the restaurant
        ratings = [review.rating for review in self.reviews]
        if ratings:
            return sum(ratings) / len(ratings)
        else:
            return 0









@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@login_manager.user_loader
def load_restaurant(restaurant_id):
    return Restaurant.query.get(int(restaurant_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        contact_number = request.form.get('contact_number')
        address = request.form.get('address')

        new_user = Users(username=username, password=password, full_name=full_name, contact_number=contact_number,
                         address=address)

        try:
            new_user.validate()
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e), 'error')

    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = Users.query.filter_by(username=username).first()

        if not user or user.password != password:
            flash('Invalid Credentials. Please try again.', 'error')
            return redirect(url_for('login'))

        login_user(user, remember=remember)
        return redirect(url_for('index'))

    return render_template('login.html')




@app.route('/')
@login_required
def index():
    try:
        restaurants = Restaurant.query.limit(3).all()
        menuitems = MenuItem.query.limit(3).all()
        return render_template('index.html', restaurants=restaurants, user=current_user, menuitems=menuitems)
    except Exception as e:
        flash('An error occurred while retrieving data.', 'error')
        return render_template('index.html', restaurants=[], user=current_user)

    

@app.route('/restaurants', methods=['GET', 'POST'])
def restaurants():
    filter_type = request.form.get('filter_type')

    if filter_type is None or filter_type == 'All':
        filter_type = 'All'
        restaurants = Restaurant.query.all()
    else:
        restaurants = Restaurant.query.filter_by(category=filter_type).all()

    return render_template('restaurants.html', restaurants=restaurants, filter_type=filter_type, user=current_user)


@app.route('/restaurant/<int:restaurant_id>/menu')
def restaurant_menu(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    if restaurant is None:
        flash('Restaurant not found.', 'error')
        return redirect(url_for('restaurants'))

    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    reviews = Review.query.filter_by(restaurant_id=restaurant_id).all()

    return render_template('restaurant_menu.html', restaurant=restaurant, menu_items=menu_items, reviews=reviews, user=current_user)

@app.route('/restaurant/<int:restaurant_id>/review', methods=['POST'])
def review(restaurant_id):
    if request.method == 'POST':
        review_text = request.form['review_text']
        rating = float(request.form['rating'])
        user_id = current_user.user_id
        
        # Check if the user has already submitted a review for this restaurant
        existing_review = Review.query.filter_by(restaurant_id=restaurant_id, user_id=user_id).first()
        
        if existing_review:
            # Update the existing review
            existing_review.review_text = review_text
            existing_review.rating = rating
        else:
            # Create a new review object
            new_review = Review(restaurant_id=restaurant_id, user_id=user_id, review_text=review_text, rating=rating)
            db.session.add(new_review)

        # Commit changes to the database
        db.session.commit()

        # Update the average rating of the restaurant
        restaurant = Restaurant.query.get(restaurant_id)
        if restaurant:
            reviews = Review.query.filter_by(restaurant_id=restaurant_id).all()
            total_rating = sum(review.rating for review in reviews)
            avg_rating = total_rating / len(reviews) if reviews else 0
            restaurant.total_rating = avg_rating
            db.session.commit()

    # Redirect back to the menu page
    return redirect(url_for('restaurant_menu', restaurant_id=restaurant_id))



@app.route('/menu_item/<int:restaurant_id>/<int:item_id>')
def menu_item(restaurant_id,item_id):

    restaurant = Restaurant.query.get(restaurant_id)
    # Query the database for the menu item details
    menu_item = MenuItem.query.get(item_id)
    if menu_item is None:
        flash('Menu item not found.', 'error')
        return redirect(url_for('index'))

    # Render the menu_item.html template with the menu item details
    return render_template('menu_item.html', menu_item=menu_item, user = current_user, restaurant=restaurant)


@app.route('/add_to_cart/<int:restaurant_id>/<int:item_id>', methods=['POST'])
@login_required
def add_to_cart(restaurant_id,item_id):
    # Get the current user ID
    
    user_id = current_user.user_id
    
    # Assuming you have a form where users can specify the quantity
    quantity = int(request.form.get('quantity'))

    # Check if the item is already present in the user's cart
    existing_cart_item = Cart.query.filter_by(user_id=user_id, item_id=item_id).first()

    if existing_cart_item:
        # If the item is already in the cart, increase the quantity
        existing_cart_item.quantity += quantity
    else:
        # If the item is not in the cart, create a new cart item
        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            flash('Menu item not found.', 'error')
            return redirect(url_for('index'))

        cart_item = Cart(user_id=user_id, item_id=item_id, quantity=quantity,restaurant_id=restaurant_id, item_image=menu_item.item_image)
        db.session.add(cart_item)

    # Commit changes to the database
    db.session.commit()

    # Redirect to the menu item page
    return redirect(url_for('menu_item', restaurant_id=restaurant_id,item_id=item_id))

@app.route("/<string:name>")
def invalid(name):
    return render_template('404.html')

@app.route('/view_cart')
@login_required
def view_cart():
    # Get the current user ID
    user_id = current_user.user_id
    
    # Query the cart items for the current user
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    # Initialize a list to store cart item details
    cart_item_details = []

    # Iterate over the cart items and fetch item details from MenuItem table
    for cart_item in cart_items:
        # Query the MenuItem table to get item details including the name
        menu_item = MenuItem.query.get(cart_item.item_id)
        
        # Create a dictionary with cart item details
        cart_item_detail = {
            'item_name': menu_item.item_name,
            'quantity': cart_item.quantity,
            'item_image': cart_item.item_image,  # Assuming item_image is stored in Cart table
            'item_id': cart_item.item_id,  # Add item_id attribute
            # Add more details as needed
        }
        # Append the cart item detail to the list
        cart_item_details.append(cart_item_detail)

    # Pass the cart item details to the template
    return render_template('cart.html', cart_items=cart_item_details, user=current_user)

@app.route('/deletefromcart/<int:item_id>', methods=['POST'])
@login_required
def delete_from_cart(item_id):
    # Get the current user ID
    user_id = current_user.user_id
    
    # Query the cart item
    cart_item = Cart.query.filter_by(user_id=user_id, item_id=item_id).first()

    if cart_item:
        # If the quantity is 1, remove the cart item
        if cart_item.quantity == 1:
            db.session.delete(cart_item)
        else:
            # If the quantity is greater than 1, decrease the quantity by 1
            cart_item.quantity -= 1

        # Commit changes to the database
        db.session.commit()

    # Redirect back to the cart page
    return redirect(url_for('view_cart'))


@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    
        # Get the current user ID
        user_id = current_user.user_id

        # Retrieve the cart items for the current user
        cart_items = Cart.query.filter_by(user_id=user_id).all()

        # Loop through cart items and add them to the orders table
        for cart_item in cart_items:
            new_order = Order(
                user_id=user_id,
                item_id=cart_item.item_id,
                restaurant_id=cart_item.restaurant_id,
                quantity=cart_item.quantity,
                total_price=calculate_total_price(cart_item.item_id, cart_item.quantity),
                payment_method='c',
                order_date=datetime.now()
            )
            db.session.add(new_order)

        # Commit the changes to the database
        db.session.commit()

        # Clear the cart after placing the order
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        # Redirect to the order success page
        return render_template('order_success.html', user=current_user)


# def get_restaurant_id(item_id):
#     # Implement this function to get the restaurant ID based on the item ID
#     # Example implementation:
#     menu_item = MenuItem.query.get(item_id)
#     if menu_item:
#         return menu_item.restaurant_id
#     return None

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    
        if request.method == 'POST':
            # Process the form submission and add order to the database

            # Redirect to order success page
            return render_template('order_success.html')

        elif request.method == 'GET':
            # Retrieve cart items from the session or database
            cart_items = session.get('cart_items')  # Assuming cart_items are stored in session

            if cart_items is None:
                flash('Your cart is empty.', 'error')
                return redirect(url_for('view_cart'))

            # Calculate total price
            total_price = sum(cart_item['price'] * cart_item['quantity'] for cart_item in cart_items)

            # Render the checkout page with cart items and total price
            return render_template('checkout.html', cart_items=cart_items, total_price=total_price)

    
        # Handle any exceptions
        flash('An error occurred while processing the checkout.', 'error')
        return redirect(url_for('index'))

    
def calculate_total_price(item_id, quantity):
    try:
        # Retrieve the item price from the database based on the item_id
        item = MenuItem.query.filter_by(item_id=item_id).first()
        if item:
            item_price = item.price
            # Calculate the total price by multiplying the item price by the quantity
            total_price = item_price * int(quantity)
            return total_price
        else:
            raise ValueError("Item not found.")
    except Exception as e:
        # Handle any exceptions or errors
        print(f"An error occurred while calculating the total price: {e}")
        return None  # Return None or handle the error accordingly


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    if session.get('was_once_logged_in'):
        del session['was_once_logged_in']

    # Delete rememberme cookie because logout_user does not do it for you.
    # response = make_response(redirect(url_for('login')))
    # response.delete_cookie('remember_token') 
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


paypalrestsdk.configure({
    "mode": "sandbox",  # Use sandbox mode for testing
    "client_id": "AVxfBU9XB_Sfrrbmo8RmZTNpB4V8R-vB01ewz5KAKZRB4VX-wq2jksKaeKrYRpMoWUmMUTym2uE6wSYX",
    "client_secret": "EIlhWzuoheFM70DnHul13XMS1CXdMTJHkmpwgICS_lwfONct3ggiR42PwhSpNI849-ZIrYcRi2Ec1Lvu"
})


#restaurant sign up 
@app.route('/restaurant/register', methods=['GET', 'POST'])
def restaurant_register():
    if request.method == 'POST':
        restaurant_name = request.form.get('restaurant_name')
        password = request.form.get('password')
        location = request.form.get('location')
        category = request.form.get('category')

        # Check if the post request has the file part
        if 'restaurant_image' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['restaurant_image']

        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        # If the file is selected and has an allowed extension
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Create a new restaurant instance
            new_restaurant = Restaurant(restaurant_name=restaurant_name, password=password, location=location, category=category, restaurant_image_path=file_path)

            try:
                db.session.add(new_restaurant)
                db.session.commit()
                flash('Restaurant sign up successful!', 'success')
                return redirect(url_for('restaurant_login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while signing up the restaurant.', 'error')

    return render_template('restaurant_signup.html')

def allowed_file(filename):
    # Check if the file has an allowed extension
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# @login_manager.user_loader
# def load_restaurant(restaurant_id):
#     return Restaurant.query.get(int(restaurant_id))


@app.route('/restaurant/login', methods=['GET', 'POST'])
def restaurant_login():
    if request.method == 'POST':
        restaurant_name = request.form.get('restaurant_name')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        restaurant = Restaurant.query.filter_by(restaurant_name=restaurant_name).first()

        if not restaurant or restaurant.password != password:
            flash('Invalid credentials. Please try again.', 'error')
            return redirect(url_for('restaurant_login'))

        login_user(restaurant, remember=remember)
        return redirect(url_for('restaurant_home'))

    return render_template('restaurant_login.html')


@app.route('/restauranthome')
def restaurant_home():
    # Assuming you have a way to get the current logged-in restaurant user
    # For example, if you're using Flask-Login, you can access the current_user
    # Replace 'current_user' with the actual method to get the logged-in user
    current_restaurant = current_user  # Change this to get the current logged-in restaurant
    reviews = Review.query.filter_by(restaurant_id=current_restaurant.restaurant_id).all()

    # Assuming you have a method to get the menu items for the current restaurant
    # Replace 'get_menu_items' with the actual method to get menu items
    menu_items = MenuItem.query.filter_by(restaurant_id=current_restaurant.restaurant_id).all()

    return render_template('restauranthome.html', restaurant=current_restaurant, menu_items=menu_items, reviews = reviews)

@app.route('/toggle_availability/<int:item_id>', methods=['POST'])
@login_required
def toggle_availability(item_id):
    item = MenuItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Toggle item availability
    item.is_available = not item.is_available
    db.session.commit()

    return jsonify({'message': 'Availability toggled successfully'})


@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        item_name = request.form['item_name']
        description = request.form['description']
        price = float(request.form['price'])
        is_available = True if 'is_available' in request.form else False
        
        # Handle file upload
        if 'item_image' in request.files:
            item_image = request.files['item_image']
            if item_image.filename != '':
                # Save image to UPLOAD_FOLDER
                filename = secure_filename(item_image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                item_image.save(filepath)
            else:
                filepath = None
        else:
            filepath = None
        
        # Create new MenuItem object
        new_item = MenuItem(
            restaurant_id=current_user.restaurant_id,
            item_name=item_name,
            description=description,
            price=price,
            item_image=filepath,
            is_available=is_available
        )
        
        # Add new item to database
        db.session.add(new_item)
        db.session.commit()
        
        flash('New menu item added successfully!', 'success')
        return redirect(url_for('restaurant_home'))
    
    return render_template('add_item.html')


from flask import request, redirect, url_for

@app.route('/remove_item', methods=['GET', 'POST'])
def remove_item():
    if request.method == 'POST':
        # Get the item ID from the form data
        item_id = request.form.get('item_id')

        # Find the item in the database
        menu_item = MenuItem.query.get(item_id)

        if menu_item:
            # Delete the item from the database
            db.session.delete(menu_item)
            db.session.commit()
            flash('Item removed successfully!', 'success')
        else:
            flash('Item not found.', 'error')

        # Redirect back to the restaurant menu page
        return redirect(url_for('restaurant_home'))

    # If the request method is GET, redirect to the homepage
    return redirect(url_for('index'))

    

@app.route('/update_item/<int:item_id>', methods=['GET', 'POST'])
def update_item(item_id):
    # Retrieve the menu item from the database
    item = MenuItem.query.get(item_id)

    if item:
        if request.method == 'POST':
            # Handle form submission for updating the item
            item_name = request.form['item_name']
            description = request.form['description']
            price = float(request.form['price'])
            is_available = True if 'is_available' in request.form else False
            
            # Handle file upload
            if 'item_image' in request.files:
                item_image = request.files['item_image']
                if item_image.filename != '':
                    # Save image to UPLOAD_FOLDER
                    filename = secure_filename(item_image.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    item_image.save(filepath)
                    item.item_image = filepath
            
            # Update item attributes
            item.item_name = item_name
            item.description = description
            item.price = price
            item.is_available = is_available
            
            # Commit changes to the database
            db.session.commit()
            
            flash('Menu item updated successfully!', 'success')
            return redirect(url_for('restaurant_home'))
        
        # Render the update_item.html template with the item details
        return render_template('update_item.html', item=item)
    else:
        flash('Menu item not found.', 'error')
        return redirect(url_for('restaurant_home'))

@app.route('/view_orders')
def view_orders():
    # Retrieve all orders from the database
    orders = Order.query.filter_by(restaurant_id=current_user.restaurant_id).all()

    # Create a list to store order details
    order_details = []

    # Iterate through each order to gather details
    for order in orders:
        # Retrieve user details
        user = Users.query.get(order.user_id)
        username = user.full_name if user else "Unknown"

        # Retrieve item details
        item = MenuItem.query.get(order.item_id)
        item_name = item.item_name if item else "Unknown"
        item_image = item.item_image if item else None

        # Append order details to the list
        order_details.append({
            'order_id': order.order_id,
            'username': username,
            'item_name': item_name,
            'item_image': item_image,
            'quantity': order.quantity,
            'total_price': order.total_price,
            'payment_method': order.payment_method,
            'order_date': order.order_date
        })

    # Render view_orders.html with order details
    return render_template('view_orders.html', orders=order_details)

from sqlalchemy import func
from sqlalchemy import func, extract

@app.route('/view_analytics')
def view_analytics():
   
        # Fetch the order data from the database
        orders_data = db.session.query(func.count(Order.order_id), extract('day', Order.order_date)).group_by(extract('day', Order.order_date)).all()
        
        # Prepare data for the graph
        labels = []
        data = []
        for order_count, order_day in orders_data:
            labels.append(order_day)
            data.append(order_count)

        # Render the analytics template with the data
        return render_template('analytics.html', labels=labels, data=data)
    


# Route for restaurant logout
@app.route('/restaurant/logout')
def restaurant_logout():
      # Clear the restaurant session
    session.pop('restaurant_id', None)  # Remove restaurant ID from session
    session.clear()
    logout_user()
      # Clear the current user session as well
    return redirect(url_for('restaurant_login'))  # Redirect to the home page

if __name__ == "__main__":
    app.run(debug=True)
