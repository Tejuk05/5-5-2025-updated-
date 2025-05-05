import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt
import re
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

# Helper functions (same as before)
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
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        business_name = request.form.get('business_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        user_type = request.form.get('user_type', '')

        # Validation (same as before)
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
                    error = "Email is already registered."
                else:
                    cursor.execute("INSERT INTO users (name, email, password, phone, user_type) VALUES (%s, %s, %s, %s, %s)",
                                   (name, email, hashed_password, phone, user_type))
                    mysql.connection.commit()

                    user_id = cursor.lastrowid

                    if user_type == 'seller':
                        cursor.execute("INSERT INTO sellers (user_id, business_name) VALUES (%s, %s)",
                                       (user_id, business_name))
                        mysql.connection.commit()

                    flash(f"Registration successful as {user_type.capitalize()}!", "success")
                    return redirect(url_for('login'))

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
                            return redirect(url_for('business_detail'))
                        else:
                            return redirect(url_for('user_dashboard'))
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

        license_filename = None
        id_proof_filename = None
        tax_docs_filename = None

        # File Upload Handling
        try:
            if license_file and allowed_file(license_file.filename) and len(license_file.read()) <= MAX_FILE_SIZE:
                license_file.seek(0)  # Reset file pointer
                license_filename = secure_filename(license_file.filename)
                license_file.save(os.path.join(app.config['UPLOAD_FOLDER'], license_filename))
            elif license_file:
                flash("Invalid business license file or file size exceeded.", "error")

            if id_proof_file and allowed_file(id_proof_file.filename) and len(id_proof_file.read()) <= MAX_FILE_SIZE:
                id_proof_file.seek(0)
                id_proof_filename = secure_filename(id_proof_file.filename)
                id_proof_file.save(os.path.join(app.config['UPLOAD_FOLDER'], id_proof_filename))
            elif id_proof_file:
                flash("Invalid ID proof file or file size exceeded.", "error")

            if tax_docs_file and allowed_file(tax_docs_file.filename) and len(tax_docs_file.read()) <= MAX_FILE_SIZE:
                tax_docs_file.seek(0)
                tax_docs_filename = secure_filename(tax_docs_file.filename)
                tax_docs_file.save(os.path.join(app.config['UPLOAD_FOLDER'], tax_docs_filename))
            elif tax_docs_file:
                flash("Invalid tax documents file or file size exceeded.", "error")

            if not business_name or not business_type or not business_address or not tax_id or not business_description:
                error = "All business details are required."
            else:
                cursor = mysql.connection.cursor()
                user_id = session['user_id']
                try:
                    cursor.execute("""
                        UPDATE sellers
                        SET business_name = %s,
                            business_type = %s,
                            business_address = %s,
                            tax_id = %s,
                            business_description = %s,
                            business_license = %s,
                            id_proof = %s,
                            tax_documents = %s
                        WHERE user_id = %s
                    """, (business_name, business_type, business_address, tax_id, business_description,
                          license_filename, id_proof_filename, tax_docs_filename, user_id))
                    mysql.connection.commit()
                    success = "Business details and documents uploaded successfully!"
                except Exception as e:
                    error = f"Database error: {e}"
                    mysql.connection.rollback()
                finally:
                    cursor.close()

        except Exception as e:
            error = f"File upload error: {e}"

    return render_template('business_detail.html', error=error, success=success)

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' in session and session['user_type'] == 'user':
        return "Welcome to User Dashboard!"
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

if __name__ == '__main__':
    # Create the upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)