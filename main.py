import sqlite3
import bcrypt
from customtkinter import *
from PIL import Image
from tkinter import messagebox


class HomepageWindow(CTk):
    def __init__(self, fullname, login_app):
        super().__init__()
        self.title("Homepage - User")
        self.login_app = login_app
        self.setup_window(fullname)

    def setup_window(self, fullname):
        window_width, window_height = 500, 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_left = int(screen_width / 2 - window_width / 2)
        self.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")
        self.resizable(False, False)

        CTkLabel(master=self, text=f"Welcome, {fullname}!", font=("Arial", 18)).place(relx=0.5, rely=0.4, anchor="center")
        CTkButton(master=self, text="Logout", font=("Arial", 12), command=self.logout).place(relx=0.5, rely=0.6, anchor="center")

    def logout(self):
        self.login_app.deiconify()
        self.destroy()


class AdminWindow(CTk):
    def __init__(self, fullname, login_app):
        super().__init__()
        self.title("Homepage - Admin")
        self.login_app = login_app
        self.setup_window(fullname)

    def setup_window(self, fullname):
        window_width, window_height = 500, 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_left = int(screen_width / 2 - window_width / 2)
        self.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")
        self.resizable(False, False)

        CTkLabel(master=self, text=f"Admin Panel - Welcome, {fullname}!", font=("Arial", 18)).place(relx=0.5, rely=0.4, anchor="center")
        CTkButton(master=self, text="Logout", font=("Arial", 12), command=self.logout).place(relx=0.5, rely=0.6, anchor="center")

    def logout(self):
        self.login_app.deiconify()
        self.destroy()

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


class LoginApp(CTk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        window_width, window_height = 350, 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_left = int(screen_width / 2 - window_width / 2)
        self.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")
        self.resizable(False, False)

    def create_widgets(self):
        image_path = "images/prdp_logo.png"
        image = CTkImage(dark_image=Image.open(image_path), size=(150, 150))
        image_label = CTkLabel(master=self, image=image, text="")
        image_label.place(relx=0.5, rely=0.3, anchor="center")

        self.username_entry = CTkEntry(master=self, placeholder_text="Username", font=("Arial", 12), text_color="white", width=300)
        self.username_entry.place(relx=0.5, rely=0.5, anchor="center")

        self.password_entry = CTkEntry(master=self, placeholder_text="Password", font=("Arial", 12), text_color="white", width=300, show="*")
        self.password_entry.place(relx=0.5, rely=0.6, anchor="center")

        CTkButton(master=self, text="LOGIN", font=("Arial", 12), text_color="white", width=200, command=self.login).place(relx=0.5, rely=0.7, anchor="center")
        CTkButton(master=self, text="REGISTER", font=("Arial", 12), text_color="white", width=200, command=self.open_registration_window).place(relx=0.5, rely=0.8, anchor="center")

    def open_registration_window(self):
        RegistrationWindow(self)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter your username and password!")
            return

        try:
            conn = sqlite3.connect("vswa_db.db")
            cursor = conn.cursor()
            cursor.execute("SELECT fullname, password, role FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
                fullname, role = user[0], user[2]
                messagebox.showinfo("Login Successful", f"Welcome, {fullname}!")
                self.withdraw()

                if role == "ADMIN":
                    admin_panel = AdminWindow(fullname, self)
                    admin_panel.mainloop()
                else:
                    homepage = HomepageWindow(fullname, self)
                    homepage.mainloop()
            else:
                messagebox.showerror("Error", "Invalid username or password!")
        except Exception as e:
            messagebox.showerror("Error", f"An error has occurred: {e}")


if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()
