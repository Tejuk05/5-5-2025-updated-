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

# Upload Configuration
UPLOAD_FOLDER = 'uploads'  # Create this folder in your project directory
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

mysql = MySQL(app)

# Helper functions
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) and email.endswith('.com')

def is_valid_name(name):
    return re.match(r"^[A-Za-z ]+$", name)

def is_valid_phone(phone):
    return re.match(r"^(\+91[\-\s]?)?[6789]\d{9}$", phone)

def is_valid_password(password):
    return len(password) >= 6

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        business_name = request.form.get('business_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        user_type = request.form.get('user_type', '')

        # Validate form data
        if not all([name, email, password, phone, user_type]):
            error = "All fields are required."
        elif not is_valid_name(name):
            error = "Name must contain only letters and spaces."
        elif user_type == 'seller' and not business_name:
            error = "Business name is required for sellers."
        elif not is_valid_email(email):
            error = "Invalid email address."
        elif not is_valid_password(password):
            error = "Password must be at least 6 characters long."
        elif not is_valid_phone(phone):
            error = "Invalid Indian phone number."
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor = mysql.connection.cursor()

            try:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    error = "Email is already registered. Please log in."
                    return render_template('sellerlog.html', error=error)
                else:
                    # Insert into the users table
                    cursor.execute("INSERT INTO users (name, email, password, phone, user_type) VALUES (%s, %s, %s, %s, %s)",
                                   (name, email, hashed_password, phone, user_type))
                    mysql.connection.commit()

                    user_id = cursor.lastrowid

                    session['user_id'] = user_id
                    session['user_name'] = name
                    session['user_type'] = user_type

                    if user_type == 'seller':
                        # Insert into the sellers table
                        cursor.execute("INSERT INTO sellers (user_id, business_name) VALUES (%s, %s)",
                                       (user_id, business_name))
                        mysql.connection.commit()
                        flash("Registration successful! Please provide your business details.", "success")
                        return redirect(url_for('business_detail'))
                    else:
                        flash(f"Registration successful as {user_type.capitalize()}!", "success")
                        return redirect(url_for('index'))

            except Exception as e:
                error = f"Database error: {e}"
                mysql.connection.rollback()
            finally:
                cursor.close()

    selected_role = request.args.get('role', 'seller')
    return render_template('sellerreg.html', error=error, success=success, selected_role=selected_role)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            error = "Email and password are required."
        elif not is_valid_email(email):
            error = "Invalid email format or must end with '.com'."
        else:
            cursor = mysql.connection.cursor()
            try:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                if user:
                    stored_password = user[3].encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                        session['user_id'] = user[0]
                        session['user_name'] = user[1]
                        session['user_type'] = user[5]
                        if user[5] == 'seller':
                            # Check if business details are already filled
                            cursor.execute("SELECT user_id FROM seller_profiles WHERE user_id = %s", (user[0],))
                            business_profile = cursor.fetchone()
                            if business_profile:
                                return redirect(url_for('seller_dashboard'))
                            else:
                                return redirect(url_for('business_detail'))
                        else:
                            return redirect(url_for('index'))
                    else:
                        error = "Incorrect password."
                else:
                    error = "Email ID does not exist."
            except Exception as e:
                error = f"Database error: {e}"
            finally:
                cursor.close()

    return render_template('sellerlog.html', error=error)

@app.route('/business_detail', methods=['GET', 'POST'])
def business_detail():
    if 'user_id' not in session or session['user_type'] != 'seller':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

    error = None
    success = None

    if request.method == 'POST':
        business_name = request.form.get('business_name', '').strip()
        business_type = request.form.get('business_type', '').strip()
        business_address = request.form.get('business_address', '').strip()
        tax_id = request.form.get('tax_id', '').strip()
        business_description = request.form.get('business_description', '').strip()

        license_file = request.files.get('business_license')
        id_proof_file = request.files.get('id_proof')
        tax_docs_file = request.files.get('tax_documents')
        business_image_file = request.files.get('business_image')

        license_filename = None
        id_proof_filename = None
        tax_docs_filename = None
        business_image_filename = None

        try:
            if license_file and allowed_file(license_file.filename) and len(license_file.read()) <= MAX_FILE_SIZE:
                license_file.seek(0)
                license_filename = secure_filename(license_file.filename)
                license_file.save(os.path.join(UPLOAD_FOLDER, license_filename))
            elif license_file:
                flash("Invalid business license file or file size exceeded.", "error")

            if id_proof_file and allowed_file(id_proof_file.filename) and len(id_proof_file.read()) <= MAX_FILE_SIZE:
                id_proof_file.seek(0)
                id_proof_filename = secure_filename(id_proof_file.filename)
                id_proof_file.save(os.path.join(UPLOAD_FOLDER, id_proof_filename))
            elif id_proof_file:
                flash("Invalid ID proof file or file size exceeded.", "error")

            if tax_docs_file and allowed_file(tax_docs_file.filename) and len(tax_docs_file.read()) <= MAX_FILE_SIZE:
                tax_docs_file.seek(0)
                tax_docs_filename = secure_filename(tax_docs_file.filename)
                tax_docs_file.save(os.path.join(UPLOAD_FOLDER, tax_docs_filename))
            elif tax_docs_file:
                flash("Invalid tax documents file or file size exceeded.", "error")

            if business_image_file and allowed_file(business_image_file.filename) and len(business_image_file.read()) <= MAX_FILE_SIZE:
                business_image_file.seek(0)
                business_image_filename = secure_filename(business_image_file.filename)
                business_image_file.save(os.path.join(UPLOAD_FOLDER, business_image_filename))
            elif business_image_file:
                flash("Invalid business image file or file size exceeded.", "error")

            if not all([business_name, business_type, business_address, tax_id, business_description]):
                error = "All business details are required."
            else:
                cursor = mysql.connection.cursor()
                user_id = session['user_id']

                # Check if a profile already exists for this user (shouldn't if just registered)
                cursor.execute("SELECT user_id FROM seller_profiles WHERE user_id = %s", (user_id,))
                existing_profile = cursor.fetchone()

                if existing_profile:
                    # This case should ideally not happen right after registration
                    sql = """
                        UPDATE seller_profiles SET
                            business_name = %s,
                            business_type = %s,
                            business_address = %s,
                            tax_id = %s,
                            business_description = %s,
                            business_license = %s,
                            id_proof = %s,
                            tax_documents = %s,
                            business_image = %s
                        WHERE user_id = %s
                    """
                    values = (business_name, business_type, business_address,
                              tax_id, business_description, license_filename,
                              id_proof_filename, tax_docs_filename, business_image_filename, user_id)
                    cursor.execute(sql, values)
                    mysql.connection.commit()
                    success = "Business details updated successfully!"
                else:
                    # Insert a new profile
                    sql = """
                        INSERT INTO seller_profiles (
                            user_id, business_name, business_type, business_address,
                            tax_id, business_description, business_license,
                            id_proof, tax_documents, business_image
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (user_id, business_name, business_type, business_address,
                              tax_id, business_description, license_filename,
                              id_proof_filename, tax_docs_filename, business_image_filename)
                    cursor.execute(sql, values)
                    mysql.connection.commit()
                    success = "Business details uploaded successfully!"

                flash(success, "success")
                return redirect(url_for('seller_dashboard'))

        except Exception as e:
            error = f"Database error: {e}"
            flash(error, "danger")
            mysql.connection.rollback()
            print(f"Database Error in business_detail: {e}")
        finally:
            cursor.close()

    return render_template('business_detail.html', error=error, success=success)

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session and session['user_type'] == 'seller':
        return redirect(url_for('seller_dashboard'))
    else:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' in session and session['user_type'] == 'user':
        return render_template('index.html')
    else:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_type', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/seller/upload_product', methods=['GET', 'POST'])
def upload_product():
    if 'user_id' not in session or session['user_type'] != 'seller':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'pname' not in request.form or 'description' not in request.form or 'price' not in request.form or 'quantity' not in request.form or 'image' not in request.files:
            flash('All fields are required.', 'error')
            return redirect(request.referrer)  # Redirect back to the upload form

        pname = request.form['pname']
        description = request.form['description']
        price = request.form['price']
        quantity = request.form['quantity']
        image = request.files['image']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                image.save(filepath)
                image_path_in_db = '/uploads/' + filename  # Store relative path

                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO sellproduct (seller_id, pname, description, price, image_path, quantity) VALUES (%s, %s, %s, %s, %s, %s)",
                            (session['user_id'], pname, description, price, image_path_in_db, quantity))
                mysql.connection.commit()
                cur.close()
                flash('Product uploaded successfully!', 'success')
                return redirect(url_for('seller_dashboard')) # Redirect to seller dashboard

            except Exception as e:
                flash(f'Error uploading product to database: {e}', 'error')
                return redirect(request.referrer)

        else:
            flash('Invalid file type or no image selected.', 'error')
            return redirect(request.referrer)

    return render_template('upload_product.html') # Render the upload form

@app.route('/seller/dashboard')
def seller_dashboard():
    if 'user_id' in session and session['user_type'] == 'seller':
        return render_template('seller_dashboard.html')
    else:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

# Define the missing routes for the links in your index.html
@app.route('/handicrafts')
def handicrafts():
    return render_template('index.html') # Replace with your actual handicrafts page

@app.route('/textiles')
def textiles():
    return render_template('index.html') # Replace with your actual textiles page

@app.route('/jewellery')
def jewellery():
    return render_template('index.html') # Replace with your actual jewellery page

@app.route('/pottery')
def pottery():
    return render_template('index.html') # Replace with your actual pottery page

@app.route('/culture')
def culture():
    return render_template('index.html') # Replace with your actual culture page

@app.route('/natural_oils')
def natural_oils():
    return render_template('index.html') # Replace with your actual natural oils page

@app.route('/herbal_soaps')
def herbal_soaps():
    return render_template('index.html') # Replace with your actual herbal soaps page

@app.route('/ayurvedic_products')
def ayurvedic_products():
    return render_template('index.html') # Replace with your actual ayurvedic products page

@app.route('/dishes')
def dishes():
    return render_template('index.html') # Replace with your actual regional cuisine page

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)