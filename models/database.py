import sqlite3
import bcrypt

def authenticate_user(username, password):
    try:
        conn = sqlite3.connect("vswa_db.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            return user[0], user[2]
    except Exception as e:
        print(f"Database error: {e}")
    return None
