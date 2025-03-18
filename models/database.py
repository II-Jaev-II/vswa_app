import sqlite3
import bcrypt
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller and development"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def authenticate_user(username, password):
    try:
        # Use resource_path here to ensure correct path in PyInstaller bundle
        conn = sqlite3.connect(resource_path("database/vswa_db.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            return user[0], user[2]
    except Exception as e:
        print(f"Database error: {e}")
    return None
