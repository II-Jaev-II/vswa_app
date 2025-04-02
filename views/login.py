from customtkinter import *
from PIL import Image
from tkinter import messagebox
from views.registration import RegistrationWindow
from views.contractor_homepage import HomepageWindow
from views.admin import AdminWindow
from models.database import authenticate_user
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Set appearance mode to system default (switches automatically between light and dark)
set_appearance_mode("System")
set_default_color_theme("blue")

class LoginApp(CTk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.setup_window()
        self.create_widgets()
        self.bind("<Return>", lambda event: self.login())
        self.resizable(False, False)

    def setup_window(self):
        height = 430
        width = 530
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        image_path = resource_path("images/prdp_logo.png")
        # Provide both light and dark images (using the same image here; change if needed)
        image = CTkImage(light_image=Image.open(image_path),
                         dark_image=Image.open(image_path),
                         size=(150, 150))
        image_label = CTkLabel(master=self, image=image, text="")
        image_label.place(relx=0.5, rely=0.3, anchor="center")
        
        # Removed explicit text_color so the theme manages the text colors
        self.username_entry = CTkEntry(master=self, placeholder_text="Username", font=("Arial", 12), width=300)
        self.username_entry.place(relx=0.5, rely=0.5, anchor="center")

        self.password_entry = CTkEntry(master=self, placeholder_text="Password", font=("Arial", 12), width=300, show="*")
        self.password_entry.place(relx=0.5, rely=0.6, anchor="center")

        CTkButton(master=self, text="LOGIN", font=("Arial", 12), width=200, command=self.login).place(relx=0.5, rely=0.7, anchor="center")
        CTkButton(master=self, text="REGISTER", font=("Arial", 12), width=200, command=self.open_registration_window).place(relx=0.5, rely=0.8, anchor="center")

    def open_registration_window(self):
        RegistrationWindow(self)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter your username and password!")
            return

        result = authenticate_user(username, password)
        if result:
            user_id, role = result
            self.withdraw()
            if role == "ADMIN":
                admin_panel = AdminWindow(user_id, self)
                admin_panel.mainloop()
            else:
                homepage = HomepageWindow(user_id, self)
                homepage.mainloop()
        else:
            messagebox.showerror("Error", "Invalid username or password!")
