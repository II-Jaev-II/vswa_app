import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from customtkinter import (
    CTk, CTkButton, CTkFrame, CTkLabel, CTkEntry,
    CTkComboBox
)
import sys
import os
import pandas as pd

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller and development"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_FILENAME = resource_path("database/vswa_db.db")

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

    # ─── OVERRIDE THE EXCEPTION HANDLER ────────────────────────────────
    def report_callback_exception(self, exc, val, tb):
        error_message = str(val)
        if "invalid command name" in error_message and "_click_animation" in error_message:
            return
        else:
            super().report_callback_exception(exc, val, tb)

    # ─── DATABASE HELPERS ──────────────────────────────────────────────
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

    # ─── DATA FETCHING METHODS ─────────────────────────────────────────
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
        query = "SELECT item_number, item_name, quantity, unit FROM selected_construction_items"
        rows = self._run_query(query, fetchall=True)
        return rows if rows else []

    def refresh_construction_items_table(self):
        # Clear existing rows in the scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        headers = ["Item Number", "Item Name", "Quantity", "Unit"]
        col_widths = [150, 500, 100, 100]

        header_frame = CTkFrame(self.scrollable_frame, fg_color="black")
        header_frame.pack(fill="x", padx=1, pady=1)
        for header, width in zip(headers, col_widths):
            col_label = CTkLabel(header_frame, text=header, font=("Roboto", 12, "bold"),
                                 width=width, height=30, fg_color="gray20")
            col_label.pack(side="left", padx=1, pady=1)

        selected_items = self.fetch_selected_construction_items()
        for index, item in enumerate(selected_items):
            bg_color = "#2E2E2E" if (index + 1) % 2 == 0 else "#1C1C1C"
            row_frame = CTkFrame(self.scrollable_frame, fg_color="black")
            row_frame.pack(fill="x", padx=1, pady=1)
            for value, width in zip(item, col_widths):
                cell_label = CTkLabel(row_frame, text=value, font=("Roboto", 12),
                                      width=width, height=30, fg_color=bg_color)
                cell_label.pack(side="left", padx=1, pady=1)

    # ─── UI SETUP ──────────────────────────────────────────────────────
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
        project_details = self.fetch_project_details(user_id)
        project_name = project_details.get("project_name", "N/A")
        location = project_details.get("location", "N/A")
        project_id = project_details.get("project_id", "N/A")
        contractor_name = project_details.get("contractor_name", "N/A")
        project_type = project_details.get("project_type", "N/A")

        # Logout Button
        self.logout_button = CTkButton(self, text="Logout", font=("Roboto", 12), command=self.logout)
        self.logout_button.pack(pady=5, anchor="ne", padx=10)

        # ─── Project Information Frame ──────────────────────────────
        self.info_frame = CTkFrame(self, corner_radius=10, fg_color="#11151f")
        self.info_frame.pack(pady=10, padx=10, fill="x")

        # Top bar for the Edit button
        self.top_frame = CTkFrame(self.info_frame, fg_color="#11151f")
        self.top_frame.pack(fill="x")
        self.edit_button = CTkButton(self.top_frame, text="Edit", font=("Roboto", 12), command=self.enable_editing)
        self.edit_button.pack(side="right", padx=10, pady=5)

        self.row_project_name = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_project_name.pack(fill="x", padx=10, pady=2)
        self.project_name_label = CTkLabel(self.row_project_name, text="NAME OF PROJECT:", font=("Roboto", 12, "bold"))
        self.project_name_label.pack(side="left")
        self.project_name_value = CTkLabel(self.row_project_name, text=project_name, font=("Roboto", 12, "bold"))
        self.project_name_value.pack(side="left", padx=10)

        self.row_location = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_location.pack(fill="x", padx=10, pady=2)
        self.location_label = CTkLabel(self.row_location, text="LOCATION:", font=("Roboto", 12, "bold"))
        self.location_label.pack(side="left")
        self.location_value = CTkLabel(self.row_location, text=location, font=("Roboto", 12, "bold"))
        self.location_value.pack(side="left", padx=10)

        self.row_project_id = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_project_id.pack(fill="x", padx=10, pady=2)
        self.project_id_label = CTkLabel(self.row_project_id, text="PROJECT ID:", font=("Roboto", 12, "bold"))
        self.project_id_label.pack(side="left")
        self.project_id_value = CTkLabel(self.row_project_id, text=project_id, font=("Roboto", 12, "bold"))
        self.project_id_value.pack(side="left", padx=10)

        self.row_contractor = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_contractor.pack(fill="x", padx=10, pady=2)
        self.contractor_label = CTkLabel(self.row_contractor, text="CONTRACTOR:", font=("Roboto", 12, "bold"))
        self.contractor_label.pack(side="left")
        self.contractor_value = CTkLabel(self.row_contractor, text=contractor_name, font=("Roboto", 12, "bold"))
        self.contractor_value.pack(side="left", padx=10)

        self.row_project_type = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_project_type.pack(fill="x", padx=10, pady=2)
        self.project_type_label = CTkLabel(self.row_project_type, text="PROJECT TYPE:", font=("Roboto", 12, "bold"))
        self.project_type_label.pack(side="left")
        self.project_type_value = CTkLabel(self.row_project_type, text=project_type, font=("Roboto", 12, "bold"))
        self.project_type_value.pack(side="left", padx=10)

        # ─── Separate Frame for the Upload Excel Button ─────────────
        self.upload_frame = CTkFrame(self, corner_radius=10)
        self.upload_frame.pack(pady=10, padx=10, fill="x")
        self.upload_button = CTkButton(
            self.upload_frame,
            text="Upload POW",
            font=("Roboto", 12),
            command=self.upload_excel
        )
        self.upload_button.pack(side="left", padx=10, pady=5)

        # ─── Construction Items List Frame ──────────────────────────
        self.extra_frame = CTkFrame(self, corner_radius=10, fg_color="#11151f")
        self.extra_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.extra_label = CTkLabel(self.extra_frame, text="List of Construction Items", font=("Roboto", 16, "bold"))
        self.extra_label.pack(pady=10)

        self.table_container = tk.Frame(self.extra_frame, bd=2, relief="solid")
        self.table_container.pack(padx=10, pady=10, fill="both", expand=True)

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

        self.refresh_construction_items_table()

    # ─── UPLOAD EXCEL FUNCTIONALITY ─────────────────────────────────────
    def upload_excel(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not file_path:
            return  # User cancelled
        
        try:
            # Read the Excel file with header on row 38 (0-indexed 37)
            df = pd.read_excel(file_path, header=37)
            # Clean up headers by stripping extra spaces/newlines.
            df.columns = [str(col).strip() for col in df.columns]
            # Check for required columns
            has_item_no = "Item No." in df.columns
            has_scope_of_work = "Scope of Work" in df.columns
            has_quantity = "Quantity" in df.columns
            has_unit = "Unit" in df.columns
            
            if not (has_item_no or has_scope_of_work or has_quantity or has_unit):
                messagebox.showwarning(
                    "Missing Columns",
                    "Neither 'Item No.' nor 'Scope of Work' nor 'Quantity' nor 'Unit' was found in the Excel file."
                )
                return
            
            # Remove rows where all required columns are empty.
            df = df.dropna(how="all", subset=[col for col in ["Item No.", "Scope of Work", "Quantity", "Unit"] if col in df.columns])
            # Create the selected_construction_items table if it doesn't exist
            create_table_query = """
                CREATE TABLE IF NOT EXISTS selected_construction_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_number TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity TEXT NOT NULL,
                    unit TEXT NOT NULL
                )
            """
            self._run_query(create_table_query, commit=True)
            # Insert query for adding a record
            insert_query = """
                INSERT INTO selected_construction_items 
                (user_id, item_number, item_name, quantity, unit)
                VALUES (?, ?, ?, ?, ?)
            """
            for _, row in df.iterrows():
                item_no_value = str(row["Item No."]) if has_item_no and pd.notna(row["Item No."]) else "N/A"
                scope_value = str(row["Scope of Work"]) if has_scope_of_work and pd.notna(row["Scope of Work"]) else "N/A"
                quantity_value = str(row["Quantity"]) if has_quantity and pd.notna(row["Quantity"]) else "N/A"
                unit_value = str(row["Unit"]) if has_unit and pd.notna(row["Unit"]) else "N/A"
                self._run_query(
                    insert_query,
                    params=(self.current_user_id, item_no_value, scope_value, quantity_value, unit_value),
                    commit=True
                )
            messagebox.showinfo(
                "Success",
                "Excel file uploaded and data inserted into selected_construction_items!"
            )
            self.refresh_construction_items_table()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # ─── PROJECT DETAILS EDITING ─────────────────────────────────────────
    def enable_editing(self):
        self.project_name_value.pack_forget()
        self.location_value.pack_forget()
        self.project_id_value.pack_forget()
        self.contractor_value.pack_forget()
        self.project_type_value.pack_forget()
        self.edit_button.pack_forget()

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

        self.project_name_value.configure(text=new_project_name)
        self.location_value.configure(text=new_location)
        self.project_id_value.configure(text=new_project_id)
        self.contractor_value.configure(text=new_contractor)
        self.project_type_value.configure(text=new_project_type)

        self.cancel_editing()

    def cancel_editing(self):
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

        self.project_name_value.pack(side="left", padx=10)
        self.location_value.pack(side="left", padx=10)
        self.project_id_value.pack(side="left", padx=10)
        self.contractor_value.pack(side="left", padx=10)
        self.project_type_value.pack(side="left", padx=10)
        self.edit_button.pack(side="right", padx=10, pady=5)

    # ─── WINDOW HANDLING ────────────────────────────────────────────────
    def on_close(self):
        self.logout()

    def logout(self):
        self.logout_button.configure(state="disabled")
        if self.login_app:
            self.login_app.deiconify()
        self.withdraw()
        self.after(200, self.destroy)