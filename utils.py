# Lưu tin nhắn vào database
from eventlet.green import MySQLdb
from flask_login import current_user

from config import mysql


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

# Truy vấn username từ sender_id
def get_username(sender_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # ✅ Kết nối DB
    cursor.execute("SELECT username FROM users WHERE id = %s", (sender_id,))
    result = cursor.fetchone()
    cursor.close()  # ✅ Đóng cursor
    return result["username"] if result else "Người dùng ẩn danh"