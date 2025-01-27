import tkinter as tk
from tkinter import messagebox
import sqlite3

# Database Setup
def setup_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Function to handle login
def login():
    username = username_entry.get()
    password = password_entry.get()

    if not username or not password:
        messagebox.showerror("Error", "All fields are required!")
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        messagebox.showinfo("Success", f"Welcome, {username}!")
        open_homepage(username)  # Redirect to homepage
        root.destroy()  # Close the login window
    else:
        messagebox.showerror("Error", "Invalid username or password")

# Function to open the registration window
def open_registration():
    def register():
        reg_username = reg_username_entry.get()
        reg_password = reg_password_entry.get()

        if not reg_username or not reg_password:
            messagebox.showerror("Error", "All fields are required!")
            return

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (reg_username, reg_password))
            conn.commit()
            messagebox.showinfo("Success", "User registered successfully!")
            registration_window.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        finally:
            conn.close()

    registration_window = tk.Toplevel(root)
    registration_window.title("Register")
    registration_window.geometry("300x200")

    tk.Label(registration_window, text="Username:").pack(pady=5)
    reg_username_entry = tk.Entry(registration_window)
    reg_username_entry.pack(pady=5)

    tk.Label(registration_window, text="Password:").pack(pady=5)
    reg_password_entry = tk.Entry(registration_window, show="*")
    reg_password_entry.pack(pady=5)

    tk.Button(registration_window, text="Register", command=register).pack(pady=10)

# Function to open the homepage
def open_homepage(username):
    homepage = tk.Tk()
    homepage.title("Homepage")
    homepage.geometry("400x300")

    tk.Label(homepage, text=f"Welcome, {username}!", font=("Arial", 16)).pack(pady=20)
    tk.Label(homepage, text="This is your homepage.", font=("Arial", 12)).pack(pady=10)

    tk.Button(homepage, text="Logout", command=lambda: [homepage.destroy(), main()]).pack(pady=20)

    homepage.mainloop()

# Main GUI
def main():
    global root, username_entry, password_entry

    root = tk.Tk()
    root.title("Login")
    root.geometry("300x200")

    tk.Label(root, text="Username:").pack(pady=5)
    username_entry = tk.Entry(root)
    username_entry.pack(pady=5)

    tk.Label(root, text="Password:").pack(pady=5)
    password_entry = tk.Entry(root, show="*")
    password_entry.pack(pady=5)

    tk.Button(root, text="Login", command=login).pack(pady=10)
    tk.Button(root, text="Register", command=open_registration).pack(pady=5)

    root.mainloop()

# Initialize database and run the application
setup_database()
main()
