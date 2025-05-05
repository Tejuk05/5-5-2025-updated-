from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Tej@shwini05'#V@r$ha#123
app.config['MYSQL_DB'] = 'desi'

mysql = MySQL(app)

# Helper functions
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) and email.endswith('.com')

def is_valid_password(password):
    return (len(password) >= 8 and
            re.search(r"[A-Z]", password) and
            re.search(r"[a-z]", password) and
            re.search(r"[0-9]", password) and
            re.search(r"[^a-zA-Z0-9\s]", password))

# User Registration Route
@app.route('/userreg', methods=['GET', 'POST'])
def user_register():
    error = None
    success = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not all([name, email, password]):
            error = "All fields are required."
        elif not re.match(r"^[A-Za-z ]+$", name):
            error = "Name must contain only letters and spaces."
        elif not is_valid_email(email):
            error = "Invalid email address."
        elif not is_valid_password(password):
            error = "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character."
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                error = "Email is already registered."
            else:
                cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'user')",
                               (name, email, hashed_password))
                mysql.connection.commit()
                flash("Registration successful!", "success")
                return redirect(url_for('userlog'))
            cursor.close()

    return render_template('userreg.html', error=error, success=success)

# User Login Route
@app.route('/userlog', methods=['GET', 'POST'])
def user_login():
    error = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            error = "Email and password are required."
        elif not is_valid_email(email):
            error = "Invalid email address."
        # Note: We don't re-validate the password complexity here during login,
        # we only check if the entered password matches the hashed one.
        else:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s AND role = 'user'", (email,))
            user = cursor.fetchone()
            cursor.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash("Login successful!", "success")
                return redirect(url_for('user_dashboard'))
            else:
                error = "Invalid email or password."

    return render_template('userlog.html', error=error)

# User Dashboard Route (example protected route)
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' in session:
        return f"Welcome, {session['username']}! This is your dashboard."
    else:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('user_login'))

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# Redirect to user registration as the main index
@app.route('/')
def index():
    return redirect(url_for('user_register'))

# ✅ Run the app
if __name__ == '__main__':
    app.run(debug=True)