from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Tej@shwini05'
app.config['MYSQL_DB'] = 'desi'

mysql = MySQL(app)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'  # Create this folder in your project
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_popular_products_from_db():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT DISTINCT id, pname, description, price, image_path FROM sellproduct")
        products = cur.fetchall()
        cur.close()
        return products
    except Exception as e:
        flash(f'Error fetching products: {e}', 'danger')
        return []

@app.route('/')
def home():
    popular_products = get_popular_products_from_db()
    return render_template('index.html', popular_products=popular_products, active_tab='home')

@app.route('/handicrafts')
def handicrafts():
    return render_template('handicrafts.html', active_tab='shop')

@app.route('/textiles')
def textiles():
    return render_template('textiles.html', active_tab='shop')

@app.route('/jewellery')
def jewellery():
    return render_template('jewellery.html', active_tab='shop')

@app.route('/pottery')
def pottery():
    return render_template('pottery.html', active_tab='shop')

@app.route('/culture')
def culture():
    return render_template('culture.html', active_tab='culture')

@app.route('/skincare')
def skincare():
    return render_template('skincare.html', active_tab='skincare')

@app.route('/natural_oils')
def natural_oils():
    return render_template('natural_oils.html', active_tab='skincare')

@app.route('/herbal_soaps')
def herbal_soaps():
    return render_template('herbal_soaps.html', active_tab='skincare')

@app.route('/ayurvedic_products')
def ayurvedic_products():
    return render_template('ayurvedic_products.html', active_tab='skincare')

@app.route('/dishes')
def dishes():
    return render_template('dishes.html', active_tab='dishes')

@app.route('/recipe')
def recipe():
    return render_template('recipe.html', active_tab='recipe')

# Example route to handle product uploads (you'll need a form for this)
@app.route('/upload_product', methods=['POST'])
def upload_product():
    if 'pname' in request.form and 'description' in request.form and 'price' in request.form and 'image' in request.files:
        pname = request.form['pname']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            try:
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO sellproduct (pname, description, price, image_path) VALUES (%s, %s, %s, %s)",
                            (pname, description, price, '/static/uploads/' + filename))
                mysql.connection.commit()
                cur.close()
                flash('Product uploaded successfully!', 'success')
                return redirect(url_for('home'))
            except Exception as e:
                flash(f'Error uploading product to database: {e}', 'danger')
                return redirect(url_for('home'))
        else:
            flash('Invalid file type or no file selected.', 'warning')
            return redirect(url_for('home'))
    else:
        flash('Missing product details.', 'warning')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)