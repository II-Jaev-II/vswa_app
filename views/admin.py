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

    # ─── OVERRIDE THE EXCEPTION HANDLER TO IGNORE THE CLICK ANIMATION ERROR ───
    def report_callback_exception(self, exc, val, tb):
        error_message = str(val)
        if "invalid command name" in error_message and "_click_animation" in error_message:
            # Ignore the error that comes from the click animation callback
            return
        else:
            super().report_callback_exception(exc, val, tb)

    # ─── DATABASE HELPERS ────────────────────────────────────────────────
    def _run_query(self, query, params=(), commit=False, fetchone=False, fetchall=False):
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
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x_position = (screen_width - width) // 2
        y_position = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x_position}+{y_position}")

    # ─── DATA FETCHING METHODS ───────────────────────────────────────────
    def fetch_user_id(self, user_id):
        query = "SELECT id FROM users WHERE user_id = ?"
        result = self._run_query(query, (user_id,), fetchone=True)
        return result[0] if result else None

    def fetch_project_details(self, user_id):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT project_name, location, project_id, contractor_name, project_type "
                "FROM project_informations LIMIT 1"
            )
            row = cursor.fetchone()
            return dict(zip(["project_name", "location", "project_id", "contractor_name", "project_type"], row)) if row else {}
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error fetching project details: {e}")
            return {}
        finally:
            conn.close()

    def fetch_selected_construction_items(self):
        query = """
            SELECT ct.name, sci.item_number, sci.item_name
            FROM selected_construction_items sci
            JOIN construction_types ct ON sci.construction_type_id = ct.id
        """
        rows = self._run_query(query, fetchall=True)
        return rows if rows else []

    def refresh_construction_items_table(self):
        # Clear existing rows in the scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        headers = ["Construction Type", "Item Number", "Item Name"]
        col_widths = [200, 100, 500]

        # Recreate header row (using pack inside a frame)
        header_frame = CTkFrame(self.scrollable_frame, fg_color="black")
        header_frame.pack(fill="x", padx=1, pady=1)
        for header, width in zip(headers, col_widths):
            col_label = CTkLabel(header_frame, text=header, font=("Roboto", 12, "bold"),
                                 width=width, height=30, fg_color="gray20")
            col_label.pack(side="left", padx=1, pady=1)

        selected_items = self.fetch_selected_construction_items()

        # Populate rows
        for index, item in enumerate(selected_items):
            bg_color = "#2E2E2E" if (index + 1) % 2 == 0 else "#1C1C1C"
            row_frame = CTkFrame(self.scrollable_frame, fg_color="black")
            row_frame.pack(fill="x", padx=1, pady=1)
            for value, width in zip(item, col_widths):
                cell_label = CTkLabel(row_frame, text=value, font=("Roboto", 12),
                                      width=width, height=30, fg_color=bg_color)
                cell_label.pack(side="left", padx=1, pady=1)

    # ─── UI SETUP ─────────────────────────────────────────────────────────
    def setup_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.75)
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.resizable(False, False)

    def create_widgets(self, user_id):
        # Fetch project details
        project_details = self.fetch_project_details(user_id)
        project_name = project_details.get("project_name", "N/A")
        location = project_details.get("location", "N/A")
        project_id = project_details.get("project_id", "N/A")
        contractor_name = project_details.get("contractor_name", "N/A")
        project_type = project_details.get("project_type", "N/A")

        # Logout Button
        self.logout_button = CTkButton(self, text="Logout", font=("Roboto", 12), command=self.logout)
        self.logout_button.pack(pady=5, anchor="ne", padx=10)

        # Information Frame using pack
        self.info_frame = CTkFrame(self, corner_radius=10, fg_color="#11151f")
        self.info_frame.pack(pady=10, padx=10, fill="x")

        # Top bar for edit button
        self.top_frame = CTkFrame(self.info_frame, fg_color="#11151f")
        self.top_frame.pack(fill="x")
        self.edit_button = CTkButton(self.top_frame, text="Edit", font=("Roboto", 12), command=self.enable_editing)
        self.edit_button.pack(side="right", padx=10, pady=5)

        # Row for project name
        self.row_project_name = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_project_name.pack(fill="x", padx=10, pady=2)
        self.project_name_label = CTkLabel(self.row_project_name, text="NAME OF PROJECT:", font=("Roboto", 12, "bold"))
        self.project_name_label.pack(side="left")
        self.project_name_value = CTkLabel(self.row_project_name, text=project_name, font=("Roboto", 12, "bold"))
        self.project_name_value.pack(side="left", padx=10)

        # Row for location
        self.row_location = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_location.pack(fill="x", padx=10, pady=2)
        self.location_label = CTkLabel(self.row_location, text="LOCATION:", font=("Roboto", 12, "bold"))
        self.location_label.pack(side="left")
        self.location_value = CTkLabel(self.row_location, text=location, font=("Roboto", 12, "bold"))
        self.location_value.pack(side="left", padx=10)

        # Row for project ID
        self.row_project_id = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_project_id.pack(fill="x", padx=10, pady=2)
        self.project_id_label = CTkLabel(self.row_project_id, text="PROJECT ID:", font=("Roboto", 12, "bold"))
        self.project_id_label.pack(side="left")
        self.project_id_value = CTkLabel(self.row_project_id, text=project_id, font=("Roboto", 12, "bold"))
        self.project_id_value.pack(side="left", padx=10)

        # Row for contractor
        self.row_contractor = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_contractor.pack(fill="x", padx=10, pady=2)
        self.contractor_label = CTkLabel(self.row_contractor, text="CONTRACTOR:", font=("Roboto", 12, "bold"))
        self.contractor_label.pack(side="left")
        self.contractor_value = CTkLabel(self.row_contractor, text=contractor_name, font=("Roboto", 12, "bold"))
        self.contractor_value.pack(side="left", padx=10)

        # Row for project type
        self.row_project_type = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_project_type.pack(fill="x", padx=10, pady=2)
        self.project_type_label = CTkLabel(self.row_project_type, text="PROJECT TYPE:", font=("Roboto", 12, "bold"))
        self.project_type_label.pack(side="left")
        self.project_type_value = CTkLabel(self.row_project_type, text=project_type, font=("Roboto", 12, "bold"))
        self.project_type_value.pack(side="left", padx=10)

        # Add Items Button
        self.add_item_button = CTkButton(self, text="Add Items", font=("Roboto", 12), command=self.show_construction_types)
        self.add_item_button.pack(padx=10, pady=3, anchor="w")

        # Extra Frame for List of Added Construction Items
        self.extra_frame = CTkFrame(self, corner_radius=10, fg_color="#11151f")
        self.extra_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.extra_label = CTkLabel(self.extra_frame, text="List of Construction Items", font=("Roboto", 16, "bold"))
        self.extra_label.pack(pady=10)

        self.table_container = tk.Frame(self.extra_frame, bd=2, relief="solid")
        self.table_container.pack(padx=10, pady=10, fill="both", expand=True)

        # Create a scrollable table
        self.table_canvas = tk.Canvas(self.table_container, bg="#1C1C1C", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.table_container, orient="vertical", command=self.table_canvas.yview)
        self.scrollable_frame = CTkFrame(self.table_canvas, fg_color="#1C1C1C")

        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))
        )
        self.table_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.table_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.table_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Initially populate the table
        self.refresh_construction_items_table()

    # ─── CONSTRUCTION TYPES / ITEMS ──────────────────────────────────────
    def show_construction_types(self):
        project_details = self.fetch_project_details(self.current_user_id)
        project_type_text = project_details.get("project_type", "N/A")

        query = "SELECT id FROM project_types WHERE name = ?"
        project_type_id_result = self._run_query(query, (project_type_text,), fetchone=True)
        if not project_type_id_result:
            print("No matching project type found.")
            return
        project_type_id = project_type_id_result[0]

        query = "SELECT id, name FROM construction_types WHERE project_type_id = ?"
        construction_types = self._run_query(query, (project_type_id,), fetchall=True)

        self.items_window = CTkToplevel(self)
        self.items_window.title("Construction Items")
        window_width, window_height = 430, 530
        self._center_window(self.items_window, window_width, window_height)
        self.items_window.resizable(False, False)
        self.items_window.lift()
        self.items_window.focus()
        self.items_window.grab_set()

        if construction_types:
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
        self.construction_type_id = self.construction_type_map.get(selected_construction_type)
        query = "SELECT id, item_number, name FROM construction_items WHERE construction_type_id = ?"
        items = self._run_query(query, (self.construction_type_id,), fetchall=True)

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
        self.refresh_construction_items_table()
        self.items_window.destroy()

    # ─── PROJECT DETAILS EDITING ──────────────────────────────────────────
    def enable_editing(self):
        # Hide value labels and the edit button.
        self.project_name_value.pack_forget()
        self.location_value.pack_forget()
        self.project_id_value.pack_forget()
        self.contractor_value.pack_forget()
        self.project_type_value.pack_forget()
        self.edit_button.pack_forget()

        # Create entry fields in place of the value labels.
        self.project_name_entry = CTkEntry(self.row_project_name, font=("Roboto", 12))
        self.project_name_entry.insert(0, self.project_name_value.cget("text"))
        self.project_name_entry.pack(fill="x", padx=10, expand=True)

        self.location_entry = CTkEntry(self.row_location, font=("Roboto", 12))
        self.location_entry.insert(0, self.location_value.cget("text"))
        self.location_entry.pack(fill="x", padx=10, expand=True)

        self.project_id_entry = CTkEntry(self.row_project_id, font=("Roboto", 12))
        self.project_id_entry.insert(0, self.project_id_value.cget("text"))
        self.project_id_entry.pack(fill="x", padx=10, expand=True)

        self.contractor_entry = CTkEntry(self.row_contractor, font=("Roboto", 12))
        self.contractor_entry.insert(0, self.contractor_value.cget("text"))
        self.contractor_entry.pack(fill="x", padx=10, expand=True)

        query_types = "SELECT DISTINCT name FROM project_types"
        project_types = [row[0] for row in (self._run_query(query_types, fetchall=True) or [])]
        self.project_type_combo = CTkComboBox(self.row_project_type, font=("Roboto", 12), values=project_types)
        self.project_type_combo.set(self.project_type_value.cget("text"))
        self.project_type_combo.pack(side="left", padx=10)

        # Save and Cancel buttons (pack them into a new control row)
        self.edit_controls = CTkFrame(self.info_frame, fg_color="#11151f")
        self.edit_controls.pack(fill="x", padx=10, pady=5)
        self.save_button = CTkButton(self.edit_controls, text="Save", font=("Roboto", 12), command=self.save_changes)
        self.save_button.pack(side="left", padx=5)
        self.cancel_button = CTkButton(self.edit_controls, text="Cancel", font=("Roboto", 12), command=self.cancel_editing)
        self.cancel_button.pack(side="left", padx=5)

    def save_changes(self):
        new_project_id = self.project_id_entry.get()
        new_project_name = self.project_name_entry.get()
        new_location = self.location_entry.get()
        new_contractor = self.contractor_entry.get()
        new_project_type = self.project_type_combo.get()
        user_id = self.current_user_id

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

        current_project_id = self.project_id_value.cget("text")
        select_query = "SELECT id FROM project_informations WHERE user_id = ? AND project_id = ?"
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
                (new_project_id, new_project_name, new_location, new_contractor, new_project_type, row_id),
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
                (new_project_id, user_id, new_project_name, new_location, new_contractor, new_project_type),
                commit=True
            )

        # Update the value labels with new data.
        self.project_name_value.configure(text=new_project_name)
        self.location_value.configure(text=new_location)
        self.project_id_value.configure(text=new_project_id)
        self.contractor_value.configure(text=new_contractor)
        self.project_type_value.configure(text=new_project_type)

        self.cancel_editing()

    def cancel_editing(self):
        # Remove entry widgets and the edit control row.
        if hasattr(self, 'project_name_entry'):
            self.project_name_entry.destroy()
        if hasattr(self, 'location_entry'):
            self.location_entry.destroy()
        if hasattr(self, 'project_id_entry'):
            self.project_id_entry.destroy()
        if hasattr(self, 'contractor_entry'):
            self.contractor_entry.destroy()
        if hasattr(self, 'project_type_combo'):
            self.project_type_combo.destroy()
        if hasattr(self, 'save_button'):
            self.save_button.destroy()
        if hasattr(self, 'cancel_button'):
            self.cancel_button.destroy()
        if hasattr(self, 'edit_controls'):
            self.edit_controls.destroy()

        # Re-pack the original value labels.
        self.project_name_value.pack(side="left", padx=10)
        self.location_value.pack(side="left", padx=10)
        self.project_id_value.pack(side="left", padx=10)
        self.contractor_value.pack(side="left", padx=10)
        self.project_type_value.pack(side="left", padx=10)
        # Re-pack the edit button.
        self.edit_button.pack(side="right", padx=10, pady=5)

    # ─── WINDOW HANDLING ──────────────────────────────────────────────────
    def on_close(self):
        self.logout()

    def logout(self):
        # Disable the logout button to prevent further clicks.
        self.logout_button.configure(state="disabled")
        if self.login_app:
            self.login_app.deiconify()
        # Withdraw (hide) the window first so pending callbacks can finish,
        # then destroy the window after a short delay.
        self.withdraw()
        self.after(200, self.destroy)
