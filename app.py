from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Admin@123456'
app.config['MYSQL_DB'] = 'chat_app'

mysql = MySQL(app)

@app.route('/')
def home():
    if 'loggedin' in session:
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
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
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
def chat():
    if 'loggedin' in session:
        if request.method == 'POST':
            # Validate receiver_id
            receiver_id = request.form.get('receiver_id')
            if not receiver_id or not receiver_id.isdigit():
                flash('Vui lòng chọn người nhận!')
                return redirect(url_for('chat'))

            # Validate message
            message = request.form.get('message')
            if not message:
                flash('Vui lòng nhập tin nhắn!')
                return redirect(url_for('chat'))

            # Insert message into the database
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (%s, %s, %s)',
                           (session['id'], int(receiver_id), message))
            mysql.connection.commit()
            flash('Tin nhắn đã được gửi!')

            # Redirect to the chat page after processing the POST request
            return redirect(url_for('chat'))

        # Fetch users and messages (for GET requests)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id != %s', (session['id'],))
        users = cursor.fetchall()
        cursor.execute('''
            SELECT messages.*, users.username 
            FROM messages 
            JOIN users ON messages.sender_id = users.id 
            WHERE receiver_id = %s OR sender_id = %s 
            ORDER BY sent_at ASC
        ''', (session['id'], session['id']))
        messages = cursor.fetchall()
        return render_template('chat.html', users=users, messages=messages)
    return redirect(url_for('login'))

@app.route('/friends/')
def friends():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id != %s', (session['id'],))
        users = cursor.fetchall()
        return render_template('friends.html', users=users)
    return redirect(url_for('login'))

@app.route('/logout/')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/chat_friend/<int:friend_id>' ,methods=['GET', 'POST'])
def chat_friend(friend_id):
    if 'loggedin' in session:
        user_id = session['id']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (friend_id,))
        user = cursor.fetchone()

        # Lấy lịch sử tin nhắn giữa 2 user
        cursor.execute('''
            SELECT * FROM messages 
            WHERE (sender_id = %s AND receiver_id = %s) 
               OR (sender_id = %s AND receiver_id = %s) 
            ORDER BY sent_at ASC
        ''', (user_id, friend_id, friend_id, user_id))

        messages = cursor.fetchall()

        if request.method == 'POST':
            # Validate receiver_id
            receiver_id = friend_id

            # Validate message
            message = request.form.get('message')
            if not message:
                flash('Vui lòng nhập tin nhắn!')
                return redirect(url_for('chat_friend', friend_id=friend_id))

            # Insert message into the database
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO messages (sender_id, receiver_id, message) VALUES (%s, %s, %s)',
                           (session['id'], int(receiver_id), message))
            mysql.connection.commit()
            flash('Tin nhắn đã được gửi!')

            # Redirect to the chat page after processing the POST request
            return redirect(url_for('chat_friend', friend_id=friend_id))

        return render_template('private_chat.html', friend=user, messages=messages)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)