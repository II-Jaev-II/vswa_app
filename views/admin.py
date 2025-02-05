import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from customtkinter import (
    CTk, CTkButton, CTkFrame, CTkLabel, CTkEntry,
    CTkComboBox, CTkToplevel, CTkCheckBox
)

DB_FILENAME = "vswa_db.db"


class AdminWindow(CTk):
    def __init__(self, user_id, login_app):
        super().__init__()
        self.title("Homepage - Admin")
        self.login_app = login_app
        self.current_user_id = user_id
        self.db_filename = DB_FILENAME
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_window()
        self.create_widgets(user_id)

    # ─── DATABASE HELPERS ────────────────────────────────────────────────

    def _run_query(self, query, params=(), commit=False, fetchone=False, fetchall=False):
        """
        Helper method to run a database query.
        Returns:
            The result of cursor.fetchone() if fetchone is True,
            or cursor.fetchall() if fetchall is True,
            or None.
        """
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                if fetchone:
                    return cursor.fetchone()
                if fetchall:
                    return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        return None

    def _center_window(self, window, width, height):
        """Center a tkinter window on the screen."""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x_position = (screen_width - width) // 2
        y_position = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x_position}+{y_position}")

    # ─── DATA FETCHING METHODS ───────────────────────────────────────────

    def fetch_user_id(self, user_id):
        """Fetch user ID from the database based on the user_id."""
        query = "SELECT id FROM users WHERE user_id = ?"
        result = self._run_query(query, (user_id,), fetchone=True)
        return result[0] if result else None

    def fetch_project_details(self, user_id):
        """Retrieve the latest project details for a given user."""
        query = """
            SELECT project_id, project_name, location, contractor_name, project_type 
            FROM project_informations 
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 1
        """
        result = self._run_query(query, (user_id,), fetchone=True)
        if result:
            return {
                "project_id": result[0],
                "project_name": result[1],
                "location": result[2],
                "contractor_name": result[3],
                "project_type": result[4]
            }
        return {}

    def fetch_selected_construction_items(self):
        """Fetch selected construction items from the database."""
        query = """
            SELECT ct.name, sci.item_number, sci.item_name
            FROM selected_construction_items sci
            JOIN construction_types ct ON sci.construction_type_id = ct.id
        """
        rows = self._run_query(query, fetchall=True)
        return rows if rows else []
    
    def refresh_construction_items_table(self):
        """Clear and repopulate the construction items table with updated data."""
        # Clear all existing rows
        for row in self.construction_items_table.get_children():
            self.construction_items_table.delete(row)

        # Fetch the updated list of selected construction items
        selected_items = self.fetch_selected_construction_items()
        for index, item in enumerate(selected_items):
            # Alternate row colors
            row_tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.construction_items_table.insert("", "end", values=item, tags=(row_tag,))

    # ─── UI SETUP ─────────────────────────────────────────────────────────

    def setup_window(self):
        """Configure the main window size and grid layout."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.75)
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2

        self.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.resizable(False, False)

        # Grid configuration
        self.grid_rowconfigure(0, weight=0)  # Logout button row
        self.grid_rowconfigure(1, weight=0)  # Info frame row
        self.grid_rowconfigure(2, weight=0)  # Add Items button row
        self.grid_rowconfigure(3, weight=1)  # Table frame row
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

    def create_widgets(self, user_id):
        """Create and layout all UI widgets."""
        project_details = self.fetch_project_details(self.current_user_id)
        project_name = project_details.get("project_name", "N/A")
        location = project_details.get("location", "N/A")
        project_id = project_details.get("project_id", "N/A")
        contractor_name = project_details.get("contractor_name", "N/A")
        project_type = project_details.get("project_type", "N/A")

        # Logout Button
        self.logout_button = CTkButton(
            master=self,
            text="Logout",
            font=("Roboto", 12),
            command=self.logout
        )
        self.logout_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")

        # Information Frame
        self.info_frame = CTkFrame(master=self, corner_radius=10, fg_color="#11151f")
        self.info_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.info_frame.grid_columnconfigure(0, weight=0)
        self.info_frame.grid_columnconfigure(1, weight=1)

        # Edit Button
        self.edit_button = CTkButton(
            master=self.info_frame,
            text="Edit",
            font=("Roboto", 12),
            command=self.enable_editing
        )
        self.edit_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")

        # Project Information Labels
        self.project_name_label = CTkLabel(
            master=self.info_frame,
            text=f"NAME OF PROJECT: {project_name}",
            font=("Roboto", 12, "bold")
        )
        self.project_name_label.grid(row=1, column=0, padx=10, sticky="w")

        self.location_label = CTkLabel(
            master=self.info_frame,
            text=f"LOCATION: {location}",
            font=("Roboto", 12, "bold")
        )
        self.location_label.grid(row=2, column=0, padx=10, sticky="w")

        self.project_id_label = CTkLabel(
            master=self.info_frame,
            text=f"PROJECT ID: {project_id}",
            font=("Roboto", 12, "bold")
        )
        self.project_id_label.grid(row=3, column=0, padx=10, sticky="w")

        self.contractor_name_label = CTkLabel(
            master=self.info_frame,
            text=f"CONTRACTOR: {contractor_name}",
            font=("Roboto", 12, "bold")
        )
        self.contractor_name_label.grid(row=4, column=0, padx=10, sticky="w")

        self.project_type_label = CTkLabel(
            master=self.info_frame,
            text=f"PROJECT TYPE: {project_type}",
            font=("Roboto", 12, "bold")
        )
        self.project_type_label.grid(row=5, column=0, padx=10, sticky="w")

        # Add Items Button
        self.add_item_button = CTkButton(
            master=self,
            text="Add Items",
            font=("Roboto", 12),
            command=self.show_construction_types
        )
        self.add_item_button.grid(row=2, column=0, padx=10, pady=3, sticky="ws")

        # Extra Frame for the construction items table
        self.extra_frame = CTkFrame(master=self, corner_radius=10, fg_color="#11151f")
        self.extra_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.extra_label = CTkLabel(
            master=self.extra_frame,
            text="List of Construction Items",
            font=("Roboto", 12, "bold")
        )
        self.extra_label.pack(padx=10, pady=10)

        # Table container
        self.table_container = tk.Frame(self.extra_frame, bd=2, relief="solid")
        self.table_container.pack(padx=10, pady=10, fill="both", expand=True)

        # Treeview for construction items
        self.construction_items_table = ttk.Treeview(
            self.table_container,
            columns=("construction_type", "item_number", "item_name"),
            show="headings"
        )
        self.construction_items_table.heading("construction_type", text="Construction Type")
        self.construction_items_table.heading("item_number", text="Item Number")
        self.construction_items_table.heading("item_name", text="Item Name")
        self.construction_items_table.column("construction_type", anchor="w", width=150)
        self.construction_items_table.column("item_number", anchor="w", width=100)
        self.construction_items_table.column("item_name", anchor="w", width=100)

        # Configure alternating row colors
        self.construction_items_table.tag_configure("oddrow", background="#E8E8E8")
        self.construction_items_table.tag_configure("evenrow", background="white")

        # Insert data into the table
        selected_items = self.fetch_selected_construction_items()
        for index, item in enumerate(selected_items):
            row_tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.construction_items_table.insert("", "end", values=item, tags=(row_tag,))

        self.construction_items_table.pack(fill="both", expand=True)

    # ─── CONSTRUCTION TYPES / ITEMS ──────────────────────────────────────

    def show_construction_types(self):
        """Display a window to select construction types and items."""
        project_details = self.fetch_project_details(self.current_user_id)
        project_type_text = project_details.get("project_type", "N/A")

        # Retrieve project type ID
        query = "SELECT id FROM project_types WHERE name = ?"
        project_type_id_result = self._run_query(query, (project_type_text,), fetchone=True)
        if not project_type_id_result:
            print("No matching project type found.")
            return
        project_type_id = project_type_id_result[0]

        # Fetch construction types for the project type
        query = "SELECT id, name FROM construction_types WHERE project_type_id = ?"
        construction_types = self._run_query(query, (project_type_id,), fetchall=True)

        # Create the items window
        self.items_window = CTkToplevel(self)
        self.items_window.title("Construction Items")
        window_width, window_height = 430, 530
        self._center_window(self.items_window, window_width, window_height)
        self.items_window.resizable(False, False)
        self.items_window.lift()
        self.items_window.focus()
        self.items_window.grab_set()

        if construction_types:
            # Map construction type names to IDs
            self.construction_type_map = {name: id for id, name in construction_types}
            construction_type_names = [""] + list(self.construction_type_map.keys())

            self.construction_label = CTkLabel(
                self.items_window,
                text="Select a construction type",
                font=("Roboto", 12, "bold")
            )
            self.construction_label.pack(pady=(20, 5))

            self.combo_box = CTkComboBox(
                self.items_window,
                values=construction_type_names,
                width=300,
                command=self.update_construction_items
            )
            self.combo_box.set("")
            self.combo_box.pack(padx=10, pady=10)

            self.items_label = CTkLabel(self.items_window, text="", font=("Roboto", 12))
            self.items_label.pack(pady=10)
        else:
            self.no_items_label = CTkLabel(
                self.items_window,
                text="No construction types found.",
                font=("Roboto", 12)
            )
            self.no_items_label.pack(pady=20)

    def update_construction_items(self, selected_construction_type):
        """
        Update the UI with checkboxes for construction items based
        on the selected construction type.
        """
        self.construction_type_id = self.construction_type_map.get(selected_construction_type)
        query = "SELECT id, item_number, name FROM construction_items WHERE construction_type_id = ?"
        items = self._run_query(query, (self.construction_type_id,), fetchall=True)

        # Remove any existing items frame
        if hasattr(self, 'items_frame'):
            self.items_frame.destroy()

        self.items_frame = CTkFrame(self.items_window)
        self.items_frame.pack(pady=10, fill="both", expand=True)

        self.item_checkboxes = {}
        self.item_data_map = {}

        if items:
            for item_id, item_number, item_name in items:
                formatted_text = f"{item_number} - {item_name}"
                var = tk.IntVar()
                checkbox = CTkCheckBox(self.items_frame, text=formatted_text, variable=var)
                checkbox.pack(anchor="w", padx=10, pady=2)
                self.item_checkboxes[item_id] = var
                self.item_data_map[item_id] = {"item_number": item_number, "name": item_name}

            self.submit_button = CTkButton(
                self.items_frame,
                text="Submit",
                command=self.save_selected_items
            )
            self.submit_button.pack(pady=10)
        else:
            self.no_items_label = CTkLabel(
                self.items_frame,
                text="No items found.",
                font=("Roboto", 12)
            )
            self.no_items_label.pack(pady=10)

    def save_selected_items(self):
        """Save selected construction items to the database."""
        selected_items = [
            (
                self.current_user_id,
                self.construction_type_id,
                item_id,
                self.item_data_map[item_id]['item_number'],
                self.item_data_map[item_id]['name']
            )
            for item_id, var in self.item_checkboxes.items() if var.get()
        ]

        if not selected_items:
            messagebox.showwarning("No Selection", "No items selected.")
            return

        # Ensure the table exists
        create_table_query = """
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
        """
        self._run_query(create_table_query, commit=True)

        insert_query = """
            INSERT INTO selected_construction_items 
            (user_id, construction_type_id, item_id, item_number, item_name)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                cursor.executemany(insert_query, selected_items)
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")
            return

        messagebox.showinfo("Success", "Selected items saved successfully.")

        # Refresh the table in the main window with the new data
        self.refresh_construction_items_table()

        # Close the items window
        self.items_window.destroy()

    # ─── PROJECT DETAILS EDITING ──────────────────────────────────────────

    def enable_editing(self):
        """Enable editing of project details."""
        project_id_text = self.project_id_label.cget("text")
        current_project_id = (
            project_id_text.replace("PROJECT ID: ", "")
            if "PROJECT ID: " in project_id_text
            else ""
        )
        query = """
            SELECT project_name, location, contractor_name, project_type 
            FROM project_informations 
            WHERE project_id = ?
        """
        result = self._run_query(query, (current_project_id,), fetchone=True)

        query_types = "SELECT DISTINCT name FROM project_types"
        project_types = [row[0] for row in (self._run_query(query_types, fetchall=True) or [])]

        if result:
            project_name, location, contractor_name, project_type = result
        else:
            project_name = location = contractor_name = project_type = ""

        # Hide the Edit Button and display Save/Cancel buttons with entry fields
        self.edit_button.grid_forget()

        self.save_button = CTkButton(
            master=self.info_frame,
            text="Save",
            font=("Roboto", 12),
            command=self.save_changes
        )
        self.save_button.grid(row=0, column=0, padx=10, pady=3, sticky="w")

        self.cancel_button = CTkButton(
            master=self.info_frame,
            text="Cancel",
            font=("Roboto", 12),
            command=self.cancel_editing
        )
        self.cancel_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")

        self.project_name_entry = CTkEntry(master=self.info_frame, font=("Roboto", 12))
        self.project_name_entry.insert(0, project_name)
        self.project_name_entry.grid(row=1, column=1, padx=10, pady=3, sticky="we")

        self.location_entry = CTkEntry(master=self.info_frame, font=("Roboto", 12))
        self.location_entry.insert(0, location)
        self.location_entry.grid(row=2, column=1, padx=10, pady=3, sticky="we")

        self.project_id_entry = CTkEntry(master=self.info_frame, font=("Roboto", 12))
        self.project_id_entry.insert(0, current_project_id)
        self.project_id_entry.grid(row=3, column=1, padx=10, pady=3, sticky="we")

        self.contractor_name_entry = CTkEntry(master=self.info_frame, font=("Roboto", 12))
        self.contractor_name_entry.insert(0, contractor_name)
        self.contractor_name_entry.grid(row=4, column=1, padx=10, pady=3, sticky="we")

        self.project_type_combo_box = CTkComboBox(
            master=self.info_frame,
            font=("Roboto", 12),
            values=project_types
        )
        self.project_type_combo_box.set(project_type)
        self.project_type_combo_box.grid(row=5, column=1, padx=10, pady=3, sticky="we")

    def save_changes(self):
        """Save changes made to project details."""
        new_project_id = self.project_id_entry.get()
        project_name = self.project_name_entry.get()
        location = self.location_entry.get()
        contractor_name = self.contractor_name_entry.get()
        project_type = self.project_type_combo_box.get()
        user_id = self.current_user_id

        # Ensure the project_informations table exists
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS project_informations (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                project_id TEXT,
                project_name TEXT,
                location TEXT,
                contractor_name TEXT,
                project_type TEXT
            )
        '''
        self._run_query(create_table_query, commit=True)

        # Fetch existing row ID
        current_project_id = self.project_id_label.cget("text").replace("PROJECT ID: ", "")
        select_query = """
            SELECT id FROM project_informations 
            WHERE user_id = ? AND project_id = ?
        """
        result = self._run_query(select_query, (user_id, current_project_id), fetchone=True)

        if result:
            row_id = result[0]
            update_query = '''
                UPDATE project_informations
                SET project_id = ?, project_name = ?, location = ?, contractor_name = ?, project_type = ?
                WHERE id = ?
            '''
            self._run_query(
                update_query,
                (new_project_id, project_name, location, contractor_name, project_type, row_id),
                commit=True
            )
        else:
            insert_query = '''
                INSERT INTO project_informations 
                (project_id, user_id, project_name, location, contractor_name, project_type)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            self._run_query(
                insert_query,
                (new_project_id, user_id, project_name, location, contractor_name, project_type),
                commit=True
            )

        # Update UI labels
        self.project_name_label.configure(text=f"NAME OF PROJECT: {project_name}")
        self.location_label.configure(text=f"LOCATION: {location}")
        self.project_id_label.configure(text=f"PROJECT ID: {new_project_id}")
        self.contractor_name_label.configure(text=f"CONTRACTOR: {contractor_name}")
        self.project_type_label.configure(text=f"PROJECT TYPE: {project_type}")

        self.cancel_editing()

    def cancel_editing(self):
        """Cancel editing and revert to the original UI."""
        if hasattr(self, 'save_button'):
            self.save_button.grid_forget()
        if hasattr(self, 'cancel_button'):
            self.cancel_button.grid_forget()
        self.edit_button.grid(row=0, column=1, padx=10, pady=3, sticky="e")

        if hasattr(self, 'project_name_entry'):
            self.project_name_entry.grid_forget()
        if hasattr(self, 'location_entry'):
            self.location_entry.grid_forget()
        if hasattr(self, 'project_id_entry'):
            self.project_id_entry.grid_forget()
        if hasattr(self, 'contractor_name_entry'):
            self.contractor_name_entry.grid_forget()
        if hasattr(self, 'project_type_combo_box'):
            self.project_type_combo_box.grid_forget()

    # ─── WINDOW HANDLING ──────────────────────────────────────────────────

    def on_close(self):
        """Handle the window close event."""
        self.logout()

    def logout(self):
        """Logout and return to the login window."""
        if self.login_app:
            self.login_app.deiconify()
        self.destroy()
