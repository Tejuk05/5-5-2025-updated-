from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt
import re
import os
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong, random key!

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Tej@shwini05'  #  Keep this secure!
app.config['MYSQL_DB'] = 'desi'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Return rows as dictionaries

mysql = MySQL(app)

# Define the Product model (no need for SQLAlchemy with Flask-MySQLdb)
# class Product(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255), nullable=False)
#     description = db.Column(db.Text, nullable=True)
#     price = db.Column(db.Float, nullable=False)
#     category = db.Column(db.String(100), nullable=True)  # e.g., "Handicrafts", "Textiles"
#     image_path = db.Column(db.String(255), nullable=True) #store path

#     def __repr__(self):
#         return f'<Product #{self.id} - {self.name}>'

# Define the Order model.  Adjusted for direct MySQL usage.
# class Order(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(100), nullable=False)
#     phone = db.Column(db.String(20), nullable=False)
#     address = db.Column(db.String(200), nullable=False)
#     product_name = db.Column(db.String(100), nullable=False)
#     quantity = db.Column(db.Integer, nullable=False)
#     total_price = db.Column(db.Float, nullable=False)
#     order_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

#     def __repr__(self):
#         return f'<Order #{self.id} - {self.name} - {self.product_name}>'


@app.route('/place_order')
def place_order():
    """
    This route renders the "Place Order" page.
    It expects product details to be passed as URL parameters.
    """
    product_name = request.args.get('name', 'Product Name')
    quantity = request.args.get('quantity', '1')
    price = request.args.get('price', '10.00')
    total_price = float(price) * int(quantity)
    return render_template('place_order.html', product_name=product_name, quantity=quantity, total_price=total_price)



@app.route('/process_order', methods=['POST'])
def process_order():
    """
    This route handles the form submission from the "Place Order" page.
    It retrieves the order details from the form data, processes the order
    (e.g., saves to a database), and redirects to a confirmation page.
    """
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        product_name = request.form.get('product_name')
        quantity = int(request.form.get('quantity'))
        total_price = float(request.form.get('total_price'))

        # 1. Validate the data.
        if not name or not email or not phone or not address:
            return "Missing required fields", 400

        # 2. Save the order to the database using Flask-MySQLdb.
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """
                INSERT INTO orders (name, email, phone, address, product_name, quantity, total_price, order_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (name, email, phone, address, product_name, quantity, total_price, datetime.datetime.utcnow())
            )
            mysql.connection.commit()
            order_id = cur.lastrowid  # Get the ID of the newly inserted order
            cur.close()
        except Exception as e:
            print(f"Error saving order: {e}")  # Log the error
            flash("Failed to save order. Please try again.", "error")
            return redirect(url_for('place_order'))  #stay on the same page

        # 4.  Optionally, send an order confirmation email here.

        # 5. Redirect to a confirmation page.
        return redirect(url_for('order_confirmation', order_id=order_id))



@app.route('/order_confirmation/<int:order_id>')
def order_confirmation(order_id):
    """
    This route displays an order confirmation page.
    """
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()  # Fetch a single order
        cur.close()
        if not order:
            return "Order not found", 404
    except Exception as e:
        print(f"Error fetching order: {e}")
        return "Error fetching order", 500

    return render_template('order_confirmation.html', order=order)  # Pass the order details


@app.route('/add_product')
def add_product():
    return render_template('add_product.html')  # Create this template


@app.route('/create_product', methods=['POST'])
def create_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        category = request.form['category']
        image_path = request.form['image_path']

        # Insert into database
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                """
                INSERT INTO products (name, description, price, category, image_path)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, description, price, category, image_path)
            )
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            print(f"Error creating product: {e}")
            flash("Failed to create product. Please try again.", "error")
            return redirect(url_for('add_product'))

        return redirect(url_for('home'))  # Redirect to home


@app.route('/')
def home():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM products")
        products = cur.fetchall()
        cur.close()
    except Exception as e:
        print(f"Error fetching products: {e}")
        products = []  # Or handle the error as appropriate

    return render_template('place_order.html', products=products)



if __name__ == '__main__':
    app.run(debug=True)
