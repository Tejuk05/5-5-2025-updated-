from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# MySQL Configuration (replace with your actual credentials)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'your_database'

mysql = MySQL(app)

@app.route('/product/<int:product_id>')
def product_details(product_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT id, name, price, description, image, quantity FROM sellproduct WHERE id = %s", (product_id,))
        row = cursor.fetchone()

        if row:
            product = {
                'id': row[0],
                'name': row[1],
                'price': float(row[2]),
                'description': row[3],
                'image': row[4],
                'quantity': row[5]
            }
            return render_template('productdetails.html', product=product)
        else:
            flash("Product not found.", "danger")
            return redirect(url_for('product_list'))  # ✅ Fallback to the product list route
    except Exception as e:
        flash(f"Database error: {e}", "danger")
        return redirect(url_for('product_list'))  # Redirect on database error as well
    finally:
        cursor.close()

@app.route('/products')  # Assuming this is your product list route
def product_list():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT id, name, price, image FROM sellproduct")  # Adjust query as needed
        products = []
        rows = cursor.fetchall()
        for row in rows:
            products.append({
                'id': row[0],
                'name': row[1],
                'price': float(row[2]),
                'image': row[3]
            })
        return render_template('product_list.html', products=products)
    except Exception as e:
        flash(f"Error fetching products: {e}", "danger")
        return render_template('product_list.html', products=[]) # Or handle the error differently
    finally:
        cursor.close()

if __name__ == '__main__':
    app.run(debug=True)