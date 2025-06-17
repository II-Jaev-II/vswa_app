import sqlite3
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from customtkinter import CTk, CTkButton, CTkFrame, CTkLabel, CTkEntry, CTkComboBox
from tkcalendar import DateEntry  # New import for date picker
from PIL import Image, ImageTk  # Import Pillow for image handling
from datetime import datetime
import sys
import os
import pandas as pd
import zipfile

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
        self.title("Dashboard - Admin")
        self.login_app = login_app
        self.current_user_id = user_id
        self.db_filename = DB_FILENAME
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_window()
        self.create_widgets(user_id)
        # Keep references to PhotoImage objects to prevent garbage collection
        self.image_refs = []

    # ─── MOUSE WHEEL SCROLLING METHODS ───────────────────────────────
    def _bind_mousewheel(self, event):
        self.table_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _unbind_mousewheel(self, event):
        self.table_canvas.unbind_all("<MouseWheel>")
    
    def _on_mousewheel(self, event):
        self.table_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
                "SELECT project_name, location, project_id, contractor_name, project_type FROM project_informations LIMIT 1"
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
        # 1) clear out old
        for w in self.scrollable_frame.winfo_children():
            w.destroy()

        headers   = ["Item Number", "Item Name", "Quantity", "Unit"]
        min_width = [150,400,150,100]

        # 2) make a single container that we’ll grid into
        content = CTkFrame(self.scrollable_frame, fg_color="black")
        content.pack(fill="both", expand=True)

        # 3) configure four fluid columns
        for col, mw in enumerate(min_width):
            content.grid_columnconfigure(col, weight=1, minsize=mw)

        # 4) header row
        for col, txt in enumerate(headers):
            CTkLabel(content,
                    text=txt,
                    font=("Roboto",12,"bold"),
                    height=30,
                    fg_color="gray20",
                    text_color="white"
                    ).grid(row=0,
                        column=col,
                        sticky="nsew",
                        padx=1, pady=1)

        # 5) data rows
        for r, item in enumerate(self.fetch_selected_construction_items(), start=1):
            bg = "#2E2E2E" if (r%2)==0 else "#1C1C1C"
            for col, val in enumerate(item):
                CTkLabel(content,
                        text=val,
                        font=("Roboto",12),
                        height=30,
                        fg_color=bg,
                        text_color="white"
                        ).grid(row=r,
                            column=col,
                            sticky="nsew",
                            padx=1, pady=1)

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
        self.project_name_label = CTkLabel(self.row_project_name, text="NAME OF PROJECT:", font=("Roboto", 12, "bold"), text_color="white")
        self.project_name_label.pack(side="left")
        self.project_name_value = CTkLabel(self.row_project_name, text=project_name, font=("Roboto", 12, "bold"), text_color="white")
        self.project_name_value.pack(side="left", padx=10)

        self.row_location = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_location.pack(fill="x", padx=10, pady=2)
        self.location_label = CTkLabel(self.row_location, text="LOCATION:", font=("Roboto", 12, "bold"), text_color="white")
        self.location_label.pack(side="left")
        self.location_value = CTkLabel(self.row_location, text=location, font=("Roboto", 12, "bold"), text_color="white")
        self.location_value.pack(side="left", padx=10)

        self.row_project_id = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_project_id.pack(fill="x", padx=10, pady=2)
        self.project_id_label = CTkLabel(self.row_project_id, text="PROJECT ID:", font=("Roboto", 12, "bold"), text_color="white")
        self.project_id_label.pack(side="left")
        self.project_id_value = CTkLabel(self.row_project_id, text=project_id, font=("Roboto", 12, "bold"), text_color="white")
        self.project_id_value.pack(side="left", padx=10)

        self.row_contractor = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_contractor.pack(fill="x", padx=10, pady=2)
        self.contractor_label = CTkLabel(self.row_contractor, text="CONTRACTOR:", font=("Roboto", 12, "bold"), text_color="white")
        self.contractor_label.pack(side="left")
        self.contractor_value = CTkLabel(self.row_contractor, text=contractor_name, font=("Roboto", 12, "bold"), text_color="white")
        self.contractor_value.pack(side="left", padx=10)

        self.row_project_type = CTkFrame(self.info_frame, fg_color="#11151f")
        self.row_project_type.pack(fill="x", padx=10, pady=2)
        self.project_type_label = CTkLabel(self.row_project_type, text="PROJECT TYPE:", font=("Roboto", 12, "bold"), text_color="white")
        self.project_type_label.pack(side="left")
        self.project_type_value = CTkLabel(self.row_project_type, text=project_type, font=("Roboto", 12, "bold"), text_color="white")
        self.project_type_value.pack(side="left", padx=10)

        # ─── Separate Frame for the Upload Excel and View Attachments Buttons ─────────────
        self.upload_frame = CTkFrame(self, corner_radius=10)
        self.upload_frame.pack(pady=10, padx=10, fill="x")
        self.upload_button = CTkButton(
            self.upload_frame,
            text="Upload POW",
            font=("Roboto", 12),
            command=self.upload_excel
        )
        self.upload_button.pack(side="left", padx=10, pady=5)
        
        # Updated "View Attachments" button command
        self.view_button = CTkButton(
            self.upload_frame,
            text="View Attachments",
            font=("Roboto", 12),
            command=self.view_attachments
        )
        self.view_button.pack(side="left", padx=10, pady=5)

        # ─── Construction Items List Frame ──────────────────────────
        self.extra_frame = CTkFrame(self, corner_radius=10, fg_color="#11151f")
        self.extra_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.extra_label = CTkLabel(self.extra_frame, text="List of Construction Items", font=("Roboto", 16, "bold"), text_color="white")
        self.extra_label.pack(pady=10)

        self.table_container = tk.Frame(self.extra_frame, bd=2, relief="solid")
        self.table_container.pack(padx=10, pady=10, fill="both", expand=True)

        self.table_canvas = tk.Canvas(self.table_container, bg="#1C1C1C", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.table_container, orient="vertical", command=self.table_canvas.yview)
        self.scrollable_frame = CTkFrame(self.table_canvas, fg_color="#1C1C1C")
        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))
        )
        self._canvas_window = self.table_canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.table_canvas.configure(
                scrollregion=self.table_canvas.bbox("all")
            )
        )
        self.table_canvas.bind(
            "<Configure>",
            lambda e: self.table_canvas.itemconfigure(self._canvas_window,
                                                    width=e.width)
        )
        self.table_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.table_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel events when the cursor is over the canvas
        self.table_canvas.bind("<Enter>", self._bind_mousewheel)
        self.table_canvas.bind("<Leave>", self._unbind_mousewheel)

        self.refresh_construction_items_table()

    # ─── UPLOAD EXCEL FUNCTIONALITY ─────────────────────────────────────
    def upload_excel(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[
            ("Excel files (.xlsx)", "*.xlsx"),
            ("Excel files (.xls)",  "*.xls")
            ]
        )
        if not file_path:
            return  # User cancelled
        
        try:
            df = pd.read_excel(file_path, header=0)
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
            # Query to check for duplicates
            select_duplicate_query = """
                SELECT 1 FROM selected_construction_items 
                WHERE user_id = ? AND item_number = ? AND item_name = ? AND quantity = ? AND unit = ?
            """
            inserted_count = 0
            duplicate_count = 0
            for _, row in df.iterrows():
                item_no_value = str(row["Item No."]) if has_item_no and pd.notna(row["Item No."]) else "N/A"
                scope_value = str(row["Scope of Work"]) if has_scope_of_work and pd.notna(row["Scope of Work"]) else "N/A"
                quantity_value = str(row["Quantity"]) if has_quantity and pd.notna(row["Quantity"]) else "N/A"
                unit_value = str(row["Unit"]) if has_unit and pd.notna(row["Unit"]) else "N/A"
                
                duplicate = self._run_query(
                    select_duplicate_query,
                    params=(self.current_user_id, item_no_value, scope_value, quantity_value, unit_value),
                    fetchone=True
                )
                if duplicate:
                    duplicate_count += 1
                    continue
                else:
                    self._run_query(
                        insert_query,
                        params=(self.current_user_id, item_no_value, scope_value, quantity_value, unit_value),
                        commit=True
                    )
                    inserted_count += 1
            
            messagebox.showinfo(
                "Upload Complete",
                f"Excel file processed!\nNew records inserted: {inserted_count}\nDuplicate records skipped: {duplicate_count}"
            )
            self.refresh_construction_items_table()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # ─── IMAGE FILTERING AND DOWNLOAD METHODS ─────────────────────────
    def apply_date_filter(self, canvas_frame):
        start_date = self.start_date_picker.get_date()
        end_date   = self.end_date_picker.get_date()

        # Clear previous images
        for widget in canvas_frame.winfo_children():
            widget.destroy()

        # 1) Completed construction images — now including item_name
        comp_q = """
            SELECT image_before,
                   image_during,
                   image_after,
                   upload_date,
                   item_name
            FROM completed_construction_images
            WHERE upload_date BETWEEN ? AND ?
        """
        # If you DON'T have item_name in this table, instead do:
        # comp_q = """
        #     SELECT c.image_before,
        #            c.image_during,
        #            c.image_after,
        #            c.upload_date,
        #            s.item_name
        #     FROM completed_construction_images c
        #     JOIN selected_construction_items s
        #       ON c.item_number = s.item_number
        #       AND c.user_id     = s.user_id
        #     WHERE c.upload_date BETWEEN ? AND ?
        # """
        comp_rows = self._run_query(comp_q, (start_date, end_date), fetchall=True) or []

        # 2) Testing materials (unchanged)
        test_q = """
            SELECT upload_date,
                   test_name,
                   image_path
            FROM testing_images
            WHERE upload_date BETWEEN ? AND ?
        """
        test_rows = self._run_query(test_q, (start_date, end_date), fetchall=True) or []

        if not comp_rows and not test_rows:
            CTkLabel(canvas_frame,
                     text="No images found in the selected date range.",
                     font=("Roboto", 12), text_color="white"
                    ).pack(pady=20)
            return

        # Display completed shots, now showing item_name and date together
        for before, during, after, date_taken, item_name in comp_rows:
            frame = CTkFrame(canvas_frame, fg_color="#222222", corner_radius=5)
            frame.pack(pady=10, padx=10, fill="x")

            CTkLabel(frame,
                     text=f"{item_name} – {date_taken}",      # ← item name + date
                     font=("Roboto", 12, "bold"),
                     text_color="white"
                    ).pack(pady=5)

            for label_text, img_path in zip(
                    ["Before", "During", "After"],
                    [before, during, after]
                ):
                if not img_path:
                    continue
                sub = CTkFrame(frame, fg_color="#333333", corner_radius=5)
                sub.pack(side="left", padx=10, pady=10)
                CTkLabel(sub, text=label_text,
                         font=("Roboto", 12, "bold"), text_color="white"
                        ).pack(pady=5)
                if os.path.exists(img_path):
                    try:
                        img = Image.open(img_path)
                        img.thumbnail((400,300))
                        photo = ImageTk.PhotoImage(img)
                        lbl = tk.Label(sub, image=photo, bg="#333333")
                        lbl.image = photo
                        lbl.pack(padx=5, pady=5)
                        self.image_refs.append(photo)
                    except Exception as e:
                        CTkLabel(sub, text=f"Error: {e}",
                                 font=("Roboto",10), text_color="red"
                                ).pack(padx=5,pady=5)
                else:
                    CTkLabel(sub, text="File not found",
                             font=("Roboto",10), text_color="red"
                            ).pack(padx=5,pady=5)

        # Testing materials (unchanged)
        if test_rows:
            CTkLabel(canvas_frame,
                     text="Testing Materials",
                     font=("Roboto", 14, "bold"), text_color="white"
                    ).pack(pady=(20,5))
            for date_taken, test_name, img_path in test_rows:
                frame = CTkFrame(canvas_frame, fg_color="#2a2a2a", corner_radius=5)
                frame.pack(pady=10, padx=10, fill="x")
                CTkLabel(frame,
                         text=f"{date_taken} – {test_name}",
                         font=("Roboto", 12, "bold"), text_color="white"
                        ).pack(pady=5)

                if img_path:
                    sub = CTkFrame(frame, fg_color="#333333", corner_radius=5)
                    sub.pack(padx=10, pady=10)
                    if os.path.exists(img_path):
                        try:
                            img = Image.open(img_path)
                            img.thumbnail((400,300))
                            photo = ImageTk.PhotoImage(img)
                            lbl = tk.Label(sub, image=photo, bg="#333333")
                            lbl.image = photo
                            lbl.pack(padx=5, pady=5)
                            self.image_refs.append(photo)
                        except Exception as e:
                            CTkLabel(sub, text=f"Error: {e}",
                                     font=("Roboto",10), text_color="red"
                                    ).pack(padx=5,pady=5)
                    else:
                        CTkLabel(sub, text="File not found",
                                 font=("Roboto",10), text_color="red"
                                ).pack(padx=5,pady=5)

    def download_images_as_zip(self):
        start_date = self.start_date_picker.get_date()
        end_date   = self.end_date_picker.get_date()

        # Now selecting item_name as well
        comp_q = """
            SELECT image_before,
                   image_during,
                   image_after,
                   upload_date,
                   item_name
            FROM completed_construction_images
            WHERE upload_date BETWEEN ? AND ?
        """
        comp_rows = self._run_query(comp_q, (start_date, end_date), fetchall=True) or []

        # Testing materials unchanged (no item context)
        test_q = """
            SELECT upload_date, test_name, image_path
            FROM testing_images
            WHERE upload_date BETWEEN ? AND ?
        """
        test_rows = self._run_query(test_q, (start_date, end_date), fetchall=True) or []

        if not comp_rows and not test_rows:
            messagebox.showinfo("No Images", "No images found for the selected date range.")
            return

        zip_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files","*.zip")],
            title="Save images as ZIP"
        )
        if not zip_path:
            return

        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:

                # Helper to turn 'YYYY-MM-DD' into 'Month D, YYYY'
                def make_date_folder(dt):
                    try:
                        return datetime.strptime(str(dt), '%Y-%m-%d').strftime('%B %-d, %Y')
                    except ValueError:
                        return datetime.strptime(str(dt), '%Y-%m-%d').strftime('%B %d, %Y')

                # 1) Completed construction images grouped by item_name/date
                for before, during, after, date_taken, item_name in comp_rows:
                    date_folder = make_date_folder(date_taken)
                    for img_path in (before, during, after):
                        if img_path and os.path.exists(img_path):
                            # <Item Name>/<Date>/<filename>
                            arcname = os.path.join(item_name, date_folder, os.path.basename(img_path))
                            zipf.write(img_path, arcname=arcname)

                # 2) Testing materials (if you ever add item context here, you can mirror the above)
                for date_taken, test_name, img_path in test_rows:
                    if not img_path or not os.path.exists(img_path):
                        continue
                    date_folder = make_date_folder(date_taken)
                    # put them under a “Testing Materials” root
                    arcname = os.path.join("Testing Materials", date_folder, test_name, os.path.basename(img_path))
                    zipf.write(img_path, arcname=arcname)

            messagebox.showinfo("Success", f"Images successfully saved to {zip_path}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while creating ZIP: {e}")

    # ─── VIEW ATTACHMENTS WINDOW ────────────────────────────────────────
    def view_attachments(self):
        self.attachments_window = tk.Toplevel()
        self.attachments_window.title("Attachments")
        self.attachments_window.geometry("1600x800")
        self.attachments_window.resizable(False, False)
        self.attachments_window.configure(bg="#11151f")
        self.attachments_window.protocol("WM_DELETE_WINDOW", self.attachments_window.destroy)
        self.attachments_window.grab_set()

        self.attachments_window.update_idletasks()
        width, height = 1600, 800
        x = (self.attachments_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.attachments_window.winfo_screenheight() // 2) - (height // 2)
        self.attachments_window.geometry(f"{width}x{height}+{x}+{y}")

        date_frame = CTkFrame(self.attachments_window, fg_color="#222222")
        date_frame.pack(fill="x", padx=20, pady=10)

        date_range_label = CTkLabel(date_frame, text="Filter by Date Range:", font=("Roboto", 12), text_color="white")
        date_range_label.pack(side="left", padx=10)

        start_date_label = CTkLabel(date_frame, text="From:", font=("Roboto", 12), text_color="white")
        start_date_label.pack(side="left", padx=5)
        self.start_date_picker = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.start_date_picker.pack(side="left", padx=5)

        end_date_label = CTkLabel(date_frame, text="To:", font=("Roboto", 12), text_color="white")
        end_date_label.pack(side="left", padx=5)
        self.end_date_picker = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.end_date_picker.pack(side="left", padx=5)

        # Add a download button to allow packaging the images as a ZIP file.
        download_button = CTkButton(date_frame, text="Download Images as ZIP", font=("Roboto", 12), command=self.download_images_as_zip)
        download_button.pack(side="left", padx=10)

        attachments_frame = CTkFrame(self.attachments_window, fg_color="#11151f")
        attachments_frame.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(attachments_frame, bg="#11151f", highlightthickness=0)
        scrollbar = tk.Scrollbar(attachments_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = CTkFrame(canvas, fg_color="#11151f")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        filter_button = CTkButton(date_frame, text="Apply Filter", font=("Roboto", 12), command=lambda: self.apply_date_filter(scrollable_frame))
        filter_button.pack(side="left", padx=10)

        close_button = CTkButton(self.attachments_window, text="Close", font=("Roboto", 12), command=self.attachments_window.destroy)
        close_button.pack(pady=10)

        self.attachments_window.focus_force()

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

    # ─── WINDOW HANDLING ───────────────────────────────────────────────
    def on_close(self):
        self.logout()

    def logout(self):
        self.logout_button.configure(state="disabled")
        if self.login_app:
            self.login_app.deiconify()
        self.withdraw()
        self.after(200, self.destroy)
