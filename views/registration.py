import sqlite3
import bcrypt
from customtkinter import *
from PIL import Image
from tkinter import messagebox

class RegistrationWindow(CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Register")
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        # Set window dimensions and center it
        window_width, window_height = 400, 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_left = int(screen_width / 2 - window_width / 2)
        self.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")
        self.resizable(False, False)
        self.lift()  # Bring to front
        self.focus()  # Focus on the window
        self.grab_set()  # Disable interaction with main window

    def create_widgets(self):
        # Load and display the image
        image_path = "images/prdp_logo.png"
        image = CTkImage(dark_image=Image.open(image_path), size=(150, 150))
        image_label = CTkLabel(master=self, image=image, text="")
        image_label.place(relx=0.5, rely=0.3, anchor="center")

        # Registration fields
        self.fullname_entry = CTkEntry(master=self, placeholder_text="Fullname", font=("Arial", 12), text_color="white", width=300)
        self.fullname_entry.place(relx=0.5, rely=0.5, anchor="center")

        self.username_entry = CTkEntry(master=self, placeholder_text="Username", font=("Arial", 12), text_color="white", width=300)
        self.username_entry.place(relx=0.5, rely=0.6, anchor="center")

        self.password_entry = CTkEntry(master=self, placeholder_text="Password", font=("Arial", 12), text_color="white", width=300, show="*")
        self.password_entry.place(relx=0.5, rely=0.7, anchor="center")

        self.confirm_password_entry = CTkEntry(master=self, placeholder_text="Confirm Password", font=("Arial", 12), text_color="white", width=300, show="*")
        self.confirm_password_entry.place(relx=0.5, rely=0.8, anchor="center")

        # Submit button
        CTkButton(master=self, text="SUBMIT", font=("Arial", 12), text_color="white", width=200, command=self.submit_registration).place(relx=0.5, rely=0.9, anchor="center")

    def submit_registration(self):
        fullname = self.fullname_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm_password = self.confirm_password_entry.get().strip()

        if not fullname or not username or not password or not confirm_password:
            messagebox.showerror("Error", "All fields are required!")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Secure password storage

        try:
            conn = sqlite3.connect("vswa_db.db")
            cursor = conn.cursor()
            cursor.execute(""" 
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fullname TEXT NOT NULL,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'USER'
                )
            """)
            cursor.execute("INSERT INTO users (fullname, username, password, role) VALUES (?, ?, ?, ?)", 
                       (fullname, username, hashed_password, 'USER'))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Registration successful!")
            self.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")