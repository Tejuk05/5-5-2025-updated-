# app.py without using flask-wtf
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
import bcrypt
import re

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Tej@shwini05'#V@r$ha#123
app.config['MYSQL_DB'] = 'desi'

# Initialize MySQL
mysql = MySQL(app)

# Helper validation functions
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) and email.endswith('.com')

def is_valid_name(name):
    return re.match(r"^[A-Za-z ]+$", name)

def is_valid_password(password):
    return len(password) >= 6

def is_valid_phone(phone):
    return re.match(r"^(\+91[\-\s]?)?[6789]\d{9}$", phone)

# Routes
@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Manual validation
        if not name or not email or not password:
            error = "All fields are required."
        elif not is_valid_name(name):
            error = "Name must contain only letters and spaces."
        elif not is_valid_email(email):
            error = "Invalid email format or must end with '.com'."
        elif not is_valid_password(password):
            error = "Password must be at least 6 characters long."
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                error = "Email is already registered."
            else:
                cursor.execute("INSERT INTO admin (name, email, password) VALUES (%s, %s, %s)",
                               (name, email, hashed_password))
                mysql.connection.commit()
                cursor.close()
                flash("Registration successful! Please login.", "success")
                return redirect(url_for('login'))

            cursor.close()

    return render_template('register.html', error=error, success=success)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    success = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            error = "Email and password are required."
        elif not is_valid_email(email):
            error = "Invalid email format or must end with '.com'."
        else:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()

            if user:
                stored_password = user[3]
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    session['user'] = user[1]
                    return redirect(url_for('dashboard'))
                else:
                    error = "Incorrect password."
            else:
                error = "Email ID does not exist."

    return render_template('login.html', error=error, success=success)

@app.route('/dashboard')
def dashboard():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM sellproduct")
    data = cursor.fetchall()
    cursor.close()
    return render_template('dashboard.html', sellproduct=data)


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
