import sqlite3
from customtkinter import *
from tkinter import messagebox
    
class AdminWindow(CTk):
    def __init__(self, fullname, login_app):
        super().__init__()
        self.title("Homepage - Admin")
        self.login_app = login_app
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.current_user_id = self.fetch_user_id(fullname)
        if self.current_user_id is None:
            print("Error: Could not fetch user ID")
        
        self.setup_window(fullname)
        self.create_widgets()
        
    def fetch_user_id(self, fullname):
        try:
            conn = sqlite3.connect("vswa_db.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE fullname = ?", (fullname,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        
    def fetch_project_details(self, user_id):
        try:
            conn = sqlite3.connect("vswa_db.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT project_id, project_name, location, contractor_name, project_type 
                FROM project_informations WHERE user_id = ?
                ORDER BY id DESC LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "project_id": result[0],
                    "project_name": result[1],
                    "location": result[2],
                    "contractor_name": result[3],
                    "project_type": result[4]
                }
            else:
                return {}

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return {}

    def setup_window(self, fullname):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.75)

        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2

        self.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.resizable(False, False)
        self.grid_rowconfigure(0, weight=0)  # For the logout button
        self.grid_rowconfigure(1, weight=0)  # For the info_frame
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

    def create_widgets(self):
        # Fetch project details based on user_id
        project_details = self.fetch_project_details(self.current_user_id)

        # Default values if no record is found
        project_name = project_details.get("project_name", "N/A")
        location = project_details.get("location", "N/A")
        project_id = project_details.get("project_id", "N/A")
        contractor_name = project_details.get("contractor_name", "N/A")
        project_type = project_details.get("project_type", "N/A")

        # Logout Button
        self.logout_button = CTkButton(master=self, text="Logout", font=("Roboto", 12), command=self.logout)
        self.logout_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")

        # Information Frame
        self.info_frame = CTkFrame(master=self, corner_radius=10, fg_color="#11151f")
        self.info_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.info_frame.grid_columnconfigure(0, weight=0)
        self.info_frame.grid_columnconfigure(1, weight=1)

        # Edit Button
        self.edit_button = CTkButton(master=self.info_frame, text="Edit", font=("Roboto", 12), command=self.enable_editing)
        self.edit_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")

        # Project Name
        self.project_name_label = CTkLabel(master=self.info_frame, text=f"NAME OF PROJECT: {project_name}", font=("Roboto", 12))
        self.project_name_label.grid(row=1, column=0, padx=10, sticky="w")

        # Location
        self.location_label = CTkLabel(master=self.info_frame, text=f"LOCATION: {location}", font=("Roboto", 12))
        self.location_label.grid(row=2, column=0, padx=10, sticky="w")

        # Project ID
        self.project_id_label = CTkLabel(master=self.info_frame, text=f"PROJECT ID: {project_id}", font=("Roboto", 12))
        self.project_id_label.grid(row=3, column=0, padx=10, sticky="w")

        # Contractor Name
        self.contractor_name_label = CTkLabel(master=self.info_frame, text=f"CONTRACTOR: {contractor_name}", font=("Roboto", 12))
        self.contractor_name_label.grid(row=4, column=0, padx=10, sticky="w")
        
        # Project Type
        self.project_type_label = CTkLabel(master=self.info_frame, text=f"Project Type: {project_type}", font=("Roboto", 12))
        self.project_type_label.grid(row=5, column=0, padx=10, sticky="w")
        
        # Add Item Button
        self.add_item_button = CTkButton(master=self, text="Add Items", font=("Roboto", 12), command=self.show_construction_types)
        self.add_item_button.grid(row=2, column=0, padx=10, pady=3, sticky="ws")

    def show_construction_types(self):
        # Fetch project details
        project_details = self.fetch_project_details(self.current_user_id)
        project_type_text = project_details.get("project_type", "N/A")

        try:
            with sqlite3.connect("vswa_db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM project_types WHERE name = ?", (project_type_text,))
                project_type_id_result = cursor.fetchone()

                if not project_type_id_result:
                    print("No matching project type found.")
                    return

                project_type_id = project_type_id_result[0]
                cursor.execute("SELECT id, name FROM construction_types WHERE project_type_id = ?", (project_type_id,))
                construction_types = cursor.fetchall()

            # Create a new window
            self.items_window = CTkToplevel(self)
            self.items_window.title("Construction Items")
            self.items_window.geometry("430x530")
            self.items_window.resizable(False, False)

            # Center the window
            self.items_window.update_idletasks()
            screen_width = self.items_window.winfo_screenwidth()
            screen_height = self.items_window.winfo_screenheight()
            x_position = (screen_width // 2) - (430 // 2)
            y_position = (screen_height // 2) - (530 // 2)
            self.items_window.geometry(f"430x530+{x_position}+{y_position}")

            self.items_window.lift()
            self.items_window.focus()
            self.items_window.grab_set()

            if construction_types:
                # Store construction types in a dictionary for reference
                self.construction_type_map = {name: id for id, name in construction_types}

                # Prepend an empty value to the list for initial blank selection
                construction_type_names = [""] + list(self.construction_type_map.keys())

                # Label for construction type selection
                self.construction_label = CTkLabel(
                    self.items_window,
                    text="Select a construction type",
                    font=("Roboto", 12, "bold")
                )
                self.construction_label.pack(pady=(20, 5))

                # Dropdown to select a construction type
                self.combo_box = CTkComboBox(
                    self.items_window,
                    values=construction_type_names,  # Use modified list with empty value
                    width=300,
                    command=self.update_construction_items
                )
                self.combo_box.set("")  # Set default selection to empty
                self.combo_box.pack(padx=10, pady=10)

                # Label for displaying items
                self.items_label = CTkLabel(self.items_window, text="", font=("Roboto", 12))
                self.items_label.pack(pady=10)
            else:
                self.no_items_label = CTkLabel(self.items_window, text="No construction types found.", font=("Roboto", 12))
                self.no_items_label.pack(pady=20)

        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def update_construction_items(self, selected_construction_type):
        """Update the UI with checkboxes for construction items."""
        self.construction_type_id = self.construction_type_map.get(selected_construction_type)

        try:
            with sqlite3.connect("vswa_db.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, item_number, name FROM construction_items WHERE construction_type_id = ?", (self.construction_type_id,))
                items = cursor.fetchall()

            if hasattr(self, 'items_frame'):
                self.items_frame.destroy()

            self.items_frame = CTkFrame(self.items_window)
            self.items_frame.pack(pady=10, fill="both", expand=True)

            self.item_checkboxes = {}
            self.item_data_map = {}

            if items:
                for item_id, item_number, item_name in items:
                    formatted_text = f"{item_number} - {item_name}"
                    var = IntVar()
                    checkbox = CTkCheckBox(self.items_frame, text=formatted_text, variable=var)
                    checkbox.pack(anchor="w", padx=10, pady=2)
                    self.item_checkboxes[item_id] = var
                    self.item_data_map[item_id] = {"item_number": item_number, "name": item_name}

                self.submit_button = CTkButton(
                    self.items_frame, text="Submit", command=self.save_selected_items
                )
                self.submit_button.pack(pady=10)

            else:
                self.no_items_label = CTkLabel(self.items_frame, text="No items found.", font=("Roboto", 12))
                self.no_items_label.pack(pady=10)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            
    def save_selected_items(self):
        """Save selected construction items to the database and show a success message."""
        selected_items = [
            (self.current_user_id, self.construction_type_id, item_id, item_number, item_name)
            for item_id, var in self.item_checkboxes.items() if var.get()
            for item_number, item_name in [(self.item_data_map[item_id]['item_number'], self.item_data_map[item_id]['name'])]
        ]

        if not selected_items:
            messagebox.showwarning("No Selection", "No items selected.")
            return

        try:
            with sqlite3.connect("vswa_db.db") as conn:
                cursor = conn.cursor()
                cursor.execute(""" 
                    CREATE TABLE IF NOT EXISTS selected_construction_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    construction_type_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    item_number TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    FOREIGN KEY (construction_type_id) REFERENCES construction_types(id),
                    FOREIGN KEY (item_id) REFERENCES construction_items(id)
                    )
                """)
                cursor.executemany(
                    "INSERT INTO selected_construction_items (user_id, construction_type_id, item_id, item_number, item_name) "
                    "VALUES (?, ?, ?, ?, ?)", 
                    selected_items
                )
                conn.commit()
            
            messagebox.showinfo("Success", "Selected items saved successfully.")  # Show success message
            self.items_window.destroy()  # Close the window

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")

    def enable_editing(self):
        # Fetch existing data from the database
        project_text = self.project_id_label.cget("text")
        project_id = project_text.replace("PROJECT ID: ", "") if "PROJECT ID: " in project_text else ""
        try:
            conn = sqlite3.connect("vswa_db.db")
            cursor = conn.cursor()
            
            # Fetch project details
            cursor.execute("SELECT project_name, location, contractor_name, project_type FROM project_informations WHERE project_id = ?", (project_id,))
            result = cursor.fetchone()

            # Fetch project types dynamically
            cursor.execute("SELECT DISTINCT name FROM project_types")
            project_types = [row[0] for row in cursor.fetchall()]
        
            conn.close()

            if result:
                project_name, location, contractor_name, project_type = result
            else:
                project_name = location = contractor_name = project_type = ""
        except sqlite3.Error as e:
                print(f"Database error: {e}")
                project_name = location = contractor_name = project_type = ""
                project_types = []
        
        # Hide Edit Button
        self.edit_button.grid_forget()

        # Replace with Save and Cancel buttons
        self.save_button = CTkButton(master=self.info_frame, text="Save", font=("Roboto", 12), command=self.save_changes)
        self.save_button.grid(row=0, column=0, padx=10, pady=3, sticky="w")

        self.cancel_button = CTkButton(master=self.info_frame, text="Cancel", font=("Roboto", 12), command=self.cancel_editing)
        self.cancel_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")

        # Create Entry Fields
        self.project_name_entry = CTkEntry(master=self.info_frame, font=("Roboto", 12))
        self.project_name_entry.insert(0, project_name)
        self.project_name_entry.grid(row=1, column=1, padx=10, pady=3, sticky="we")

        self.location_entry = CTkEntry(master=self.info_frame, font=("Roboto", 12))
        self.location_entry.insert(0, location)
        self.location_entry.grid(row=2, column=1, padx=10, pady=3, sticky="we")

        self.project_id_entry = CTkEntry(master=self.info_frame, font=("Roboto", 12))
        self.project_id_entry.insert(0, project_id)
        self.project_id_entry.grid(row=3, column=1, padx=10, pady=3, sticky="we")

        self.contractor_name_entry = CTkEntry(master=self.info_frame, font=("Roboto", 12))
        self.contractor_name_entry.insert(0, contractor_name)
        self.contractor_name_entry.grid(row=4, column=1, padx=10, pady=3, sticky="we")
        
        self.project_type_combo_box = CTkComboBox(master=self.info_frame, font=("Roboto", 12), values=project_types)
        self.project_type_combo_box.set(project_type)
        self.project_type_combo_box.grid(row=5, column=1, padx=10, pady=3, sticky="we")

    def save_changes(self):
        new_project_id = self.project_id_entry.get()
        project_name = self.project_name_entry.get()
        location = self.location_entry.get()
        contractor_name = self.contractor_name_entry.get()
        project_type = self.project_type_combo_box.get()
        user_id = self.current_user_id  # Logged-in user's ID
        
        # Retrieve the row ID to ensure the correct record is updated
        try:
            conn = sqlite3.connect("vswa_db.db")
            cursor = conn.cursor()
            
            # Ensure the table exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_informations (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    project_id TEXT,
                    project_name TEXT,
                    location TEXT,
                    contractor_name TEXT,
                    project_type TEXT
                )
            ''')

            # Fetch the existing row ID based on user_id and project_id
            cursor.execute('''
                SELECT id FROM project_informations WHERE user_id = ? AND project_id = ?
            ''', (user_id, self.project_id_label.cget("text").replace("PROJECT ID: ", "")))

            result = cursor.fetchone()
            if result:
                row_id = result[0]  # The existing row ID
                
                # Update the record using the PRIMARY KEY (id)
                cursor.execute('''
                    UPDATE project_informations
                    SET project_id = ?, project_name = ?, location = ?, contractor_name = ?, project_type = ?
                    WHERE id = ?
                ''', (new_project_id, project_name, location, contractor_name, project_type, row_id))
            else:
                # If no row was found, insert a new one
                cursor.execute('''
                    INSERT INTO project_informations (project_id, user_id, project_name, location, contractor_name, project_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (new_project_id, user_id, project_name, location, contractor_name, project_type))

            conn.commit()
            conn.close()

            # Update UI labels
            self.project_name_label.configure(text=f"NAME OF PROJECT: {project_name}")
            self.location_label.configure(text=f"LOCATION: {location}")
            self.project_id_label.configure(text=f"PROJECT ID: {new_project_id}")
            self.contractor_name_label.configure(text=f"CONTRACTOR: {contractor_name}")
            self.project_type_label.configure(text=f"PROJECT TYPE: {project_type}")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Error: {e}")

        # Hide Entry Fields and Buttons
        self.cancel_editing()

    def cancel_editing(self):
        self.save_button.grid_forget()
        self.cancel_button.grid_forget()
        self.edit_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")

        self.project_name_entry.grid_forget()
        self.location_entry.grid_forget()
        self.project_id_entry.grid_forget()
        self.contractor_name_entry.grid_forget()
        self.project_type_combo_box.grid_forget()  # Fixed reference
        
    # def add_item(self):

    def on_close(self):
        self.logout()

    def logout(self):
        if self.login_app:
            self.login_app.deiconify()
        self.destroy()
