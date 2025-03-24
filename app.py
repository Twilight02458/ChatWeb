import eventlet

from utils import get_username, save_message, get_users, get_messages

eventlet.monkey_patch()
import os

import bcrypt

from werkzeug.utils import secure_filename

from config import mysql, login_manager, socketio, app

from flask import render_template, request, redirect, url_for, flash, session, jsonify
import MySQLdb.cursors
import re

from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import emit, join_room


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
            session['loggedin'] = True
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
    session.pop('loggedin', None)
    return redirect(url_for('login'))


@app.route("/upload", methods=["POST"])
@login_required
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Không có file nào được chọn"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Tên file không hợp lệ"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # Lưu tin nhắn với file vào database
    receiver_id = request.form.get("receiver_id")
    if not receiver_id or not receiver_id.isdigit():
        return jsonify({"error": "Người nhận không hợp lệ"}), 400

    sender_id = current_user.id
    save_message(sender_id, int(receiver_id), f"[File] {filename}")

    return jsonify({"file_url": f"/{file_path}"}), 200


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
    print(
        f"Client connected: {current_user.is_authenticated}, User ID: {current_user.id if current_user.is_authenticated else 'Unknown'}")
    if current_user.is_authenticated:
        join_room(str(current_user.id))  # Tham gia phòng của người dùng
        print(f"User {current_user.id} joined room {current_user.id}")


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

    if message_text.startswith("[File] ") and not data.get("resend", False):
        file_url = message_text.replace("[File] ", "")
        emit_data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "username": username,
            "message": f'<a href="{file_url}" target="_blank">📂 {file_url}</a>',
        }
    else:
        emit_data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "username": username,
            "message": message_text,
        }

    # Gửi tin nhắn đến người nhận
    emit("message", emit_data, room=str(receiver_id))

    # Chỉ gửi lại tin nhắn cho sender nếu sender khác receiver (tránh lặp)
    if sender_id != receiver_id:
        emit("message", emit_data, room=str(sender_id))


if __name__ == '__main__':
    socketio.run(app, debug=True)
