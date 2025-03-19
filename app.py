from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Admin@123'
app.config['MYSQL_DB'] = 'chat_app'

mysql = MySQL(app)

# Cấu hình Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Chỉ định route đăng nhập nếu chưa đăng nhập


# Tạo User model
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    @staticmethod
    def get(user_id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if user:
            return User(user['id'], user['username'])
        return None


# Load user khi đăng nhập
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        if user:
            user_obj = User(user['id'], user['username'])
            login_user(user_obj)
            return redirect(url_for('chat'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!')
    return render_template('login.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            flash('Tài khoản đã tồn tại!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Tên đăng nhập chỉ được chứa chữ cái và số!')
        else:
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
            mysql.connection.commit()
            flash('Đăng ký thành công!')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/chat/', methods=['GET', 'POST'])
@login_required  # Chỉ người dùng đã đăng nhập mới vào được
def chat():
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id')
        message = request.form.get('message')

        if not receiver_id or not receiver_id.isdigit():
            flash('Vui lòng chọn người nhận!')
            return redirect(url_for('chat'))

        if not message:
            flash('Vui lòng nhập tin nhắn!')
            return redirect(url_for('chat'))

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (%s, %s, %s)',
                       (current_user.id, int(receiver_id), message))
        mysql.connection.commit()
        flash('Tin nhắn đã được gửi!')
        return redirect(url_for('chat'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id != %s', (current_user.id,))
    users = cursor.fetchall()
    cursor.execute('''
        SELECT messages.*, users.username 
        FROM messages 
        JOIN users ON messages.sender_id = users.id 
        WHERE receiver_id = %s OR sender_id = %s 
        ORDER BY sent_at ASC
    ''', (current_user.id, current_user.id))
    messages = cursor.fetchall()

    return render_template('chat.html', users=users, messages=messages)


@app.route('/friends/')
@login_required
def friends():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id != %s', (current_user.id,))
    users = cursor.fetchall()
    return render_template('friends.html', users=users)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
