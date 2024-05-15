-- Create Users Table
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(100) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    contact_number VARCHAR(20),
    address TEXT
);

-- Create Restaurants Table
CREATE TABLE Restaurants (
    restaurant_id SERIAL PRIMARY KEY,
    restaurant_name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    total_rating DECIMAL(3, 2),
    restaurant_image_path VARCHAR(255), -- Assuming BYTEA for storing images
    password VARCHAR(100) NOT NULL
    is_open BOOLEAN DEFAULT TRUE,
    category VARCHAR(100)
);

-- Create Menu Items Table
CREATE TABLE MenuItems (
    item_id SERIAL PRIMARY KEY,
    restaurant_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(6, 2) NOT NULL,
    item_image BYTEA,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id)
);

-- Create Cart Table
CREATE TABLE Cart (
    cart_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (item_id) REFERENCES MenuItems(item_id)
);

-- Create Orders Table

CREATE TABLE Orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
	restaurant_id INT not null,
    quantity INT NOT NULL,
    total_price DECIMAL(8, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (item_id) REFERENCES MenuItems(item_id), 
	FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id)
);
-- Create Reviews Table
CREATE TABLE Reviews (
    review_id SERIAL PRIMARY KEY,
    restaurant_id INT NOT NULL,
    user_id INT NOT NULL,
    rating DECIMAL(2, 1) NOT NULL,
    review_text TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

ALTER TABLE Restaurants
ADD COLUMN status VARCHAR(20);


ALTER TABLE users
ADD COLUMN email VARCHAR(20);

alter table cart add column item_image varchar(100)


ALTER TABLE cart
ADD COLUMN restaurant_id INT,
ADD CONSTRAINT fk_cart_restaurant
FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id);  


ALTER TABLE cart
DROP CONSTRAINT cart_item_id_fkey,  -- Drop the existing foreign key constraint
ADD CONSTRAINT cart_item_id_fkey
FOREIGN KEY (item_id) REFERENCES menuitems(item_id) ON DELETE CASCADE;  -- Add the new foreign key constraint with ON DELETE CASCADE

ALTER TABLE orders
DROP CONSTRAINT orders_item_id_fkey,  -- Drop the existing foreign key constraint
ADD CONSTRAINT orders_item_id_fkey
FOREIGN KEY (item_id) REFERENCES menuitems(item_id) ON DELETE CASCADE;  -- Add the new foreign key constraint with ON DELETE CASCADE
