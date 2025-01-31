from customtkinter import *

class HomepageWindow(CTk):
    def __init__(self, login_app):
        super().__init__()
        self.title("Homepage - User")
        self.login_app = login_app
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_window(self, fullname):
        self.state("zoomed")
        self.resizable(False, False)

        CTkLabel(master=self, text=f"Welcome, {fullname}!", font=("Arial", 18)).place(relx=0.5, rely=0.4, anchor="center")
        CTkButton(master=self, text="Logout", font=("Arial", 12), command=self.logout).place(relx=0.5, rely=0.6, anchor="center")

    def on_close(self):
        self.logout()
        
    def logout(self):
        self.login_app.deiconify()
        self.destroy()