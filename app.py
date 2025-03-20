import os

import bcrypt
import eventlet
from werkzeug.utils import secure_filename

eventlet.monkey_patch()
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ⚡ Cấu hình WebSocket
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

# Cấu hình MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Admin@123'
app.config['MYSQL_DB'] = 'chat_app'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
mysql = MySQL(app)

# Cấu hình Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = str(id)  # Flask-Login yêu cầu ID là string
        self.username = username

    @staticmethod
    def get(user_id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            return User(user['id'], user['username'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/")
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
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
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
        avatar = request.files['avatar']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            flash('Tài khoản đã tồn tại!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Tên đăng nhập chỉ được chứa chữ cái và số!')
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Xử lý upload avatar
            if avatar:
                filename = secure_filename(avatar.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar.save(file_path)
                avatar_path = os.path.join('uploads', filename)
            else:
                avatar_path = None

            cursor.execute('INSERT INTO users (username, password, avatar) VALUES (%s, %s, %s)',
                           (username, hashed_password, avatar_path))
            mysql.connection.commit()
            flash('Đăng ký thành công!')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Lưu tin nhắn vào database
def save_message(sender_id, receiver_id, message):
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (%s, %s, %s)",
                   (sender_id, receiver_id, message))
    mysql.connection.commit()
    cursor.close()

# Lấy danh sách người dùng (trừ chính mình)
def get_users():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id != %s', (current_user.id,))
    users = cursor.fetchall()
    cursor.close()
    return users

# Lấy tin nhắn giữa 2 người
def get_messages():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT messages.*, users.username 
        FROM messages 
        JOIN users ON messages.sender_id = users.id 
        WHERE receiver_id = %s OR sender_id = %s 
        ORDER BY sent_at ASC
    ''', (current_user.id, current_user.id))
    messages = cursor.fetchall()
    cursor.close()
    return messages

@app.route('/chat/', methods=['GET', 'POST'])
@login_required
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

        save_message(current_user.id, int(receiver_id), message)
        flash('Tin nhắn đã được gửi!')
        return redirect(url_for('chat'))

    users = get_users()
    messages = get_messages()
    return render_template('chat.html', users=users, messages=messages)

@app.route('/friends/')
@login_required
def friends():
    users = get_users()
    return render_template('friends.html', users=users)

# Sự kiện WebSocket
@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {current_user.is_authenticated}, User ID: {current_user.id if current_user.is_authenticated else 'Unknown'}")
    if current_user.is_authenticated:
        join_room(str(current_user.id))  # Tham gia phòng của người dùng
        print(f"User {current_user.id} joined room {current_user.id}")


# Truy vấn username từ sender_id
def get_username(sender_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # ✅ Kết nối DB
    cursor.execute("SELECT username FROM users WHERE id = %s", (sender_id,))
    result = cursor.fetchone()
    cursor.close()  # ✅ Đóng cursor
    return result["username"] if result else "Người dùng ẩn danh"

@socketio.on("message")
def handle_message(data):
    sender_id = current_user.id
    receiver_id = data.get("receiver_id")
    message_text = data.get("message")

    if not receiver_id or not message_text.strip():
        print("🚫 Lỗi: Không có người nhận hoặc tin nhắn rỗng")
        return

    # Lấy username từ sender_id
    username = get_username(sender_id)

    # Lưu tin nhắn vào database
    save_message(sender_id, receiver_id, message_text)

    print(f"📨 Đang gửi tin nhắn từ {username} ({sender_id}) đến {receiver_id}: {message_text}")  # Debug 1

    emit_data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "username": username,  # ✅ Thêm username vào dữ liệu gửi đi
        "message": message_text
    }

    # Gửi tin nhắn đến người nhận
    emit("message", emit_data, room=str(receiver_id))
    print(f"✅ Đã gửi tin nhắn đến phòng {receiver_id}")  # Debug 2

    # Gửi lại tin nhắn cho người gửi
    emit("message", emit_data, room=str(sender_id))
    print(f"✅ Đã gửi tin nhắn lại cho phòng {sender_id}")  # Debug 3


if __name__ == '__main__':
    socketio.run(app, debug=True)
