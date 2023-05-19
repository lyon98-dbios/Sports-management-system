from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from werkzeug.utils import secure_filename
import threading
import os
import mysql.connector

# Create a connection to the database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
    database='lcu_database'
)

# Function to query the database
def query_db(username):
    cursor = conn.cursor()
    query = "SELECT passkey FROM Students WHERE username=%s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    else:
        return None

app = Flask(__name__, template_folder='templates')
app.secret_key = "secret_key"

# Set up file upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'

# Set up allowed file types
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

# Check if a file is an allowed file type
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Homepage
@app.route('/')
@login_required
def admin_index():
    return render_template('admin_index.html')

@app.route('/user_index')
@login_required
def user_index():
    return render_template('user_index.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'otp' in request.form:
            # Handle OTP submission
            otp = request.form['otp']
            # Process OTP here
            stored_otp = query_db(otp)
            if stored_otp is not None and stored_otp == otp:
                return redirect(url_for('registeration'))
            else:
                flash('Invalid Otp')
        else:
            # Handle username and password submission
            username = request.form['username']
            password = request.form['password']
            stored_password = query_db(username)
            # Process username and password here
            if username == 'admin' and password == 'admin':
                session['username'] = username
                return redirect(url_for('admin_index')) 
            elif stored_password is not None and stored_password == password:
                session['username'] = username
                return redirect(url_for('user_index'))                
            else:
                flash('Invalid username or password')
    # Display login form
    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Upload file
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File uploaded successfully')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type')
    return render_template('upload.html')

# Download file
@app.route('/download/<filename>')
@login_required
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Edit file
@app.route('/edit/<filename>', methods=['GET', 'POST'])
@login_required
def edit(filename):
    if request.method == 'POST':
        new_text = request.form['text']
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'w') as f:
            f.write(new_text)
            flash('File edited successfully')
            return redirect(url_for('index'))
    else:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
            text = f.read()
        return render_template('edit.html', filename=filename, text=text)

# Share file
@app.route('/share/<filename>', methods=['GET', 'POST'])
@login_required
def share(filename):
    if request.method == 'POST':
        recipient = request.form['recipient']
        # code to send the file to the recipient goes here
        flash('File shared successfully')
        return redirect(url_for('index'))
    else:
        return render_template('share.html', filename=filename)

# Delete file
@app.route('/delete/<filename>')
@login_required
def delete(filename):
    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    flash('File deleted successfully')

# Recycle bin
@app.route('/recycle-bin')
@login_required
def recycle_bin():
    deleted_files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('.'):
            continue
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.isfile(file_path):
                continue
                deleted_files.append(filename)
    return render_template('recycle-bin.html', deleted_files=deleted_files)

# Empty recycle bin
@app.route('/empty-recycle-bin')
@login_required
def empty_recycle_bin():
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        if filename.startswith('.'):
            continue
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not os.path.isfile(file_path):
                continue
                os.remove(file_path)
                flash('Recycle bin emptied successfully')
    return redirect(url_for('recycle_bin'))
