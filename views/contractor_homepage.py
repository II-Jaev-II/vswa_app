import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from customtkinter import CTk, CTkButton, CTkFrame, CTkLabel, CTkEntry, CTkScrollableFrame
from PIL import ImageTk, Image, ExifTags
import os
import shutil
import uuid
import sys
import datetime
from docx import Document
from docx.shared import Inches, Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller and development"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_FILENAME = resource_path("database/vswa_db.db")

def set_cell_width(cell, width_dxa):
    """
    Set the width of a cell.
    width_dxa: width in dxa units (1 inch = 1440 dxa)
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcW = OxmlElement('w:tcW')
    tcW.set(qn('w:w'), str(width_dxa))
    tcW.set(qn('w:type'), 'dxa')
    tcPr.append(tcW)

class HomepageWindow(CTk):
    def __init__(self, user_id, login_app):
        super().__init__()
        self.title("Homepage - Contractor")
        self.login_app = login_app
        self.current_user_id = user_id
        self.db_filename = DB_FILENAME
        self.add_image_window = None  # Reference to the image upload window
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_window()
        self.create_widgets()
        
    # ─── MOUSE WHEEL SCROLLING METHODS ───────────────────────────────
    def _bind_mousewheel(self, event):
        self.table_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _unbind_mousewheel(self, event):
        self.table_canvas.unbind_all("<MouseWheel>")
    
    def _on_mousewheel(self, event):
        self.table_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def setup_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * 0.75)
        window_height = int(screen_height * 0.75)
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2

        self.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.resizable(False, False)

    def create_widgets(self):
        project_details = self.fetch_project_details()
        project_name = project_details.get("project_name", "N/A")
        location = project_details.get("location", "N/A")
        project_id = project_details.get("project_id", "N/A")
        contractor_name = project_details.get("contractor_name", "N/A")
        project_type = project_details.get("project_type", "N/A")

        self.logout_button = CTkButton(self, text="Logout", font=("Roboto", 12), command=self.logout)
        self.logout_button.pack(pady=5, anchor="ne", padx=10)

        self.info_frame = CTkFrame(self, corner_radius=10, fg_color="#11151f")
        self.info_frame.pack(pady=10, padx=10, fill="x")

        labels_info = [
            f"NAME OF PROJECT: {project_name}",
            f"LOCATION: {location}",
            f"PROJECT ID: {project_id}",
            f"CONTRACTOR: {contractor_name}",
            f"PROJECT TYPE: {project_type}"
        ]
        for text in labels_info:
            CTkLabel(self.info_frame, text=text, font=("Roboto", 12, "bold"), text_color="white", anchor="w").pack(padx=10, pady=2, anchor="w")

        self.extra_frame = CTkFrame(self, corner_radius=10, fg_color="#11151f")
        self.extra_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.extra_label = CTkLabel(self.extra_frame, text="List of Construction Items", font=("Roboto", 16, "bold"), text_color="white")
        self.extra_label.pack(pady=10)

        self.table_container = tk.Frame(self.extra_frame, bd=2, relief="solid")
        self.table_container.pack(padx=10, pady=10, fill="both", expand=True)

        self.create_custom_table()

    def create_custom_table(self):
        self.table_canvas = tk.Canvas(self.table_container, bg="#1C1C1C", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.table_container, orient="vertical", command=self.table_canvas.yview)
        self.scrollable_frame = CTkFrame(self.table_canvas, fg_color="#1C1C1C")

        self.scrollable_frame.bind("<Configure>", lambda e: self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all")))
        self.table_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.table_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.table_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel events when the cursor is over the canvas
        self.table_canvas.bind("<Enter>", self._bind_mousewheel)
        self.table_canvas.bind("<Leave>", self._unbind_mousewheel)

        # Update Headers for the table to match the new structure.
        headers = ["Item Number", "Item Name", "Quantity", "Unit", "Actions"]
        col_widths = [150, 400, 150, 100, 150]

        header_frame = CTkFrame(self.scrollable_frame, fg_color="black")
        header_frame.grid(row=0, column=0, columnspan=len(headers), sticky="nsew", padx=1, pady=1)

        for col_index, (col_name, col_width) in enumerate(zip(headers, col_widths)):
            col_label = CTkLabel(header_frame, text=col_name, font=("Roboto", 12, "bold"), text_color="white",
                                 width=col_width, height=30, fg_color="gray20")
            col_label.grid(row=0, column=col_index, padx=1, pady=1, sticky="nsew")

        for col_index in range(len(headers)):
            self.scrollable_frame.grid_columnconfigure(col_index, weight=1)

        selected_items = self.fetch_selected_construction_items()

        for row_index, item in enumerate(selected_items, start=1):
            bg_color = "#2E2E2E" if row_index % 2 == 0 else "#1C1C1C"
            row_frame = CTkFrame(self.scrollable_frame, fg_color="black")
            row_frame.grid(row=row_index, column=0, columnspan=len(headers), sticky="nsew", padx=1, pady=1)

            # item: (item_number, item_name, quantity, unit)
            for col_index, (value, col_width) in enumerate(zip(item, col_widths[:-1])):
                cell_label = CTkLabel(row_frame, text=value, font=("Roboto", 12), text_color="white",
                                      width=col_width, height=30, fg_color=bg_color)
                cell_label.grid(row=0, column=col_index, padx=1, pady=1, sticky="nsew")

            item_number, item_name = item[0], item[1]
            add_image_button = CTkButton(
                row_frame, text="Add / Update Image", font=("Roboto", 12),
                command=lambda i=item_number, n=item_name: self.open_add_image_window(i, n),
                width=col_widths[-1], height=30
            )
            add_image_button.grid(row=0, column=4, padx=1, pady=1, sticky="nsew")

    def open_add_image_window(self, item_number, item_name):
        # If an add image window is already open, bring it to the front.
        if self.add_image_window is not None and self.add_image_window.winfo_exists():
            self.add_image_window.lift()
            return

        self.add_image_window = tk.Toplevel()
        self.add_image_window.title(f"Add / Update Image - {item_number} | {item_name}")
        self.add_image_window.geometry("1600x800")
        self.add_image_window.resizable(False, False)
        self.add_image_window.configure(bg="#11151f")
        self.add_image_window.protocol("WM_DELETE_WINDOW", self.on_add_image_window_close)

        # Center the window on the screen.
        self.add_image_window.update_idletasks()
        width, height = 1600, 800
        x = (self.add_image_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.add_image_window.winfo_screenheight() // 2) - (height // 2)
        self.add_image_window.geometry(f"{width}x{height}+{x}+{y}")

        scrollable_frame = CTkScrollableFrame(self.add_image_window, corner_radius=10, fg_color="#1C1C1C")
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)

        CTkLabel(
            scrollable_frame,
            text="Upload Construction Images",
            font=("Roboto", 20, "bold"),
            text_color="white"
        ).pack(pady=20)

        # --------------------------------------------------
        def has_gps_coordinates(filepath):
            try:
                img = Image.open(filepath)
                exif_data = img._getexif()
                if not exif_data:
                    return False
                exif_tags = {ExifTags.TAGS[k]: v for k, v in exif_data.items() if k in ExifTags.TAGS}
                if "GPSInfo" in exif_tags:
                    gps_info = exif_tags["GPSInfo"]
                    gps_tags = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_info.items()}
                    return "GPSLatitude" in gps_tags and "GPSLongitude" in gps_tags
                return False
            except Exception as e:
                print(f"Error reading EXIF data: {e}")
                return False

        def set_preview_pic(filepath, label, entry):
            try:
                img = Image.open(filepath)
                img = img.resize((350, 300))
                img = ImageTk.PhotoImage(img)
                label.config(image=img)
                label.image = img
                entry.delete(0, tk.END)
                entry.insert(0, filepath)
            except Exception as e:
                print(f"Error setting preview picture: {e}")

        def select_pic(label, entry):
            filename = filedialog.askopenfilename(
                initialdir=os.getcwd(),
                title="Select Image",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.jfif")]
            )
            if filename:
                if has_gps_coordinates(filename):
                    set_preview_pic(filename, label, entry)
                else:
                    messagebox.showwarning("Invalid Image", "Please upload a geotagged photo.")

        # --------------------------------------------------
        static_container = CTkFrame(scrollable_frame, corner_radius=10, fg_color="#2B2B2B")
        static_container.pack(pady=10, fill="x", padx=10)

        self.static_section_widgets = {}

        sections = [
            {"title": "Before", "key": "before"},
            {"title": "During", "key": "during"},
            {"title": "After", "key": "after"},
            {"title": "Station Limit/Grid", "key": "station_limits"}
        ]

        for sec in sections:
            card = CTkFrame(static_container, corner_radius=10, fg_color="#3B3B3B")
            card.pack(side="left", expand=True, fill="both", padx=10, pady=10)

            CTkLabel(card, text=sec["title"], font=("Roboto", 16, "bold"), text_color="white").pack(pady=(10, 5))

            if sec["key"] in ["before", "during", "after"]:
                preview_label = tk.Label(card, text="No Image", bg="#3B3B3B", fg="white")
                preview_label.pack(pady=5)
                path_entry = CTkEntry(card, width=200)
                path_entry.pack(pady=5)
                browse_btn = CTkButton(
                    card,
                    text="Browse",
                    width=100,
                    command=lambda lbl=preview_label, ent=path_entry: select_pic(lbl, ent)
                )
                browse_btn.pack(pady=5)
                self.static_section_widgets[sec["key"]] = {"preview_label": preview_label, "entry": path_entry}
            else:
                path_entry = CTkEntry(card, width=200)
                path_entry.pack(pady=(40, 10))
                self.static_section_widgets[sec["key"]] = {"entry": path_entry}

        # Load existing static data if available.
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS completed_construction_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    construction_type TEXT,
                    item_number TEXT,
                    item_name TEXT,
                    row_index INTEGER,
                    image_before TEXT,
                    image_during TEXT,
                    image_after TEXT,
                    station_limits TEXT,
                    report_generated INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                SELECT image_before, image_during, image_after, station_limits 
                FROM completed_construction_images 
                WHERE item_number=? AND item_name=? AND row_index=0
            """, (item_number, item_name))
            row = cursor.fetchone()
            conn.close()
            if row:
                if row[0] and os.path.exists(row[0]):
                    set_preview_pic(row[0], self.static_section_widgets["before"]["preview_label"],
                                    self.static_section_widgets["before"]["entry"])
                if row[1] and os.path.exists(row[1]):
                    set_preview_pic(row[1], self.static_section_widgets["during"]["preview_label"],
                                    self.static_section_widgets["during"]["entry"])
                if row[2] and os.path.exists(row[2]):
                    set_preview_pic(row[2], self.static_section_widgets["after"]["preview_label"],
                                    self.static_section_widgets["after"]["entry"])
                if row[3]:
                    self.static_section_widgets["station_limits"]["entry"].delete(0, tk.END)
                    self.static_section_widgets["station_limits"]["entry"].insert(0, row[3])
        except Exception as e:
            print(f"Error fetching existing images: {e}")

        # --------------------------------------------------
        CTkLabel(
            scrollable_frame,
            text="Additional Image Entries",
            font=("Roboto", 16, "bold"),
            text_color="white"
        ).pack(pady=20)

        dynamic_container = CTkFrame(scrollable_frame, corner_radius=10, fg_color="#2B2B2B")
        dynamic_container.pack(pady=10, fill="x", padx=10)

        self.dynamic_rows_entries = []

        def add_new_dynamic_row(prepopulated_data=None):
            row_card = CTkFrame(dynamic_container, corner_radius=10, fg_color="#3B3B3B")
            row_card.pack(fill="x", padx=10, pady=10)
            row_entries = {}

            phases = ["Before", "During", "After", "Station Limit/Grid"]
            for phase in phases:
                phase_frame = CTkFrame(row_card, corner_radius=10, fg_color="#4B4B4B")
                phase_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)
                CTkLabel(phase_frame, text=phase, font=("Roboto", 12, "bold"), text_color="white").pack(pady=(10, 5))
                if phase in ["Before", "During", "After"]:
                    preview_label = tk.Label(phase_frame, text="No Image", bg="#4B4B4B", fg="white")
                    preview_label.pack(pady=5)
                    path_entry = CTkEntry(phase_frame, width=150)
                    path_entry.pack(pady=5)
                    browse_btn = CTkButton(
                        phase_frame,
                        text="Browse",
                        width=80,
                        command=lambda lbl=preview_label, ent=path_entry: select_pic(lbl, ent)
                    )
                    browse_btn.pack(pady=5)
                    row_entries[phase.lower()] = path_entry
                    if prepopulated_data and prepopulated_data.get(phase.lower(), ""):
                        file_path = prepopulated_data.get(phase.lower())
                        path_entry.insert(0, file_path)
                        if os.path.exists(file_path):
                            set_preview_pic(file_path, preview_label, path_entry)
                else:
                    path_entry = CTkEntry(phase_frame, width=150)
                    path_entry.pack(pady=(40, 10))
                    row_entries["station_limits"] = path_entry
                    if prepopulated_data and prepopulated_data.get("station_limits", ""):
                        path_entry.insert(0, prepopulated_data.get("station_limits"))
            remove_btn = CTkButton(
                row_card,
                text="Remove",
                width=50,
                fg_color="red",
                hover_color="darkred",
                command=lambda: remove_dynamic_row(row_card, row_entries)
            )
            remove_btn.pack(side="left", padx=10, pady=10)
            self.dynamic_rows_entries.append(row_entries)

        def remove_dynamic_row(row_card, row_entries):
            row_card.destroy()
            if row_entries in self.dynamic_rows_entries:
                self.dynamic_rows_entries.remove(row_entries)

        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT image_before, image_during, image_after, station_limits 
                FROM completed_construction_images 
                WHERE item_number=? AND item_name=? AND row_index > 0
            """, (item_number, item_name))
            dynamic_rows_data = cursor.fetchall()
            conn.close()
            for data in dynamic_rows_data:
                prepopulated_data = {
                    "before": data[0],
                    "during": data[1],
                    "after": data[2],
                    "station_limits": data[3]
                }
                add_new_dynamic_row(prepopulated_data=prepopulated_data)
        except Exception as e:
            print("Error loading dynamic rows:", e)

        CTkButton(scrollable_frame, text="Add Row", width=150, command=add_new_dynamic_row).pack(pady=20)

        # --------------------------------------------------
        btn_frame = CTkFrame(scrollable_frame, corner_radius=10, fg_color="#2B2B2B")
        btn_frame.pack(pady=20)

        # Modified update function (removed construction_type)
        def update_all_uploaded_images(item_number, item_name, static_data, dynamic_rows):
            base_dir = os.path.join(os.getcwd(), "images")
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS completed_construction_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    construction_type TEXT,
                    item_number TEXT,
                    item_name TEXT,
                    row_index INTEGER,
                    image_before TEXT,
                    image_during TEXT,
                    image_after TEXT,
                    station_limits TEXT,
                    report_generated INTEGER DEFAULT 0,
                    upload_date TEXT
                )
            """)
            cursor.execute("""
                SELECT row_index, image_before, image_during, image_after, station_limits, report_generated
                FROM completed_construction_images 
                WHERE item_number=? AND item_name=?
            """, (item_number, item_name))
            existing_rows = cursor.fetchall()
            existing_dict = {}
            for row in existing_rows:
                existing_dict[row[0]] = row[1:]  # (image_before, image_during, image_after, station_limits, report_generated)

            def process_file(new_file, phase):
                if new_file:
                    target_dir = os.path.join(os.getcwd(), "images", phase.lower())
                    abs_target_dir = os.path.abspath(target_dir)
                    abs_new_file = os.path.abspath(new_file)
                    if abs_new_file.startswith(abs_target_dir):
                        return new_file
                    if not os.path.exists(new_file):
                        raise FileNotFoundError(f"Source file not found: {new_file}")
                    os.makedirs(target_dir, exist_ok=True)
                    original_filename = os.path.basename(new_file)
                    unique_filename = f"{os.path.splitext(original_filename)[0]}_{uuid.uuid4().hex}{os.path.splitext(original_filename)[1]}"
                    target_path = os.path.join(target_dir, unique_filename)
                    shutil.copy(new_file, target_path)
                    return target_path
                return None

            static_saved = {}
            for phase in ["before", "during", "after"]:
                file_path = static_data.get(phase, "")
                static_saved[phase] = process_file(file_path, phase) if file_path else None
            static_saved["station_limits"] = static_data.get("station_limits", "")
            new_saved_paths = {}
            new_saved_paths["0"] = static_saved

            row_index = 1
            for row_entries in self.dynamic_rows_entries:
                row_saved = {}
                for phase in ["before", "during", "after"]:
                    file_path = row_entries[phase].get().strip()
                    row_saved[phase] = process_file(file_path, phase) if file_path else None
                file_path = row_entries["station_limits"].get().strip()
                row_saved["station_limits"] = file_path if file_path else ""
                new_saved_paths[str(row_index)] = row_saved
                row_index += 1

            cursor.execute("""
                DELETE FROM completed_construction_images 
                WHERE item_number=? AND item_name=?
            """, (item_number, item_name))
            
            # Get today's date as a string in ISO format (YYYY-MM-DD)
            today = datetime.date.today().isoformat()
            
            new_data = (new_saved_paths["0"]["before"], new_saved_paths["0"]["during"], new_saved_paths["0"]["after"], new_saved_paths["0"]["station_limits"])
            if 0 in existing_dict and existing_dict[0][:4] == new_data:
                report_flag = existing_dict[0][4]
            else:
                report_flag = 0
            cursor.execute("""
                INSERT INTO completed_construction_images 
                (construction_type, item_number, item_name, row_index, image_before, image_during, image_after, station_limits, report_generated, upload_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("", item_number, item_name, 0,
                new_saved_paths["0"]["before"], new_saved_paths["0"]["during"], new_saved_paths["0"]["after"],
                new_saved_paths["0"]["station_limits"], report_flag, today))

            for i in range(1, row_index):
                row_data = new_saved_paths[str(i)]
                new_data = (row_data["before"], row_data["during"], row_data["after"], row_data["station_limits"])
                if i in existing_dict and existing_dict[i][:4] == new_data:
                    report_flag = existing_dict[i][4]
                else:
                    report_flag = 0
                cursor.execute("""
                    INSERT INTO completed_construction_images 
                    (construction_type, item_number, item_name, row_index, image_before, image_during, image_after, station_limits, report_generated, upload_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, ("", item_number, item_name, i,
                    row_data["before"], row_data["during"], row_data["after"], row_data["station_limits"], report_flag, today))
            conn.commit()
            conn.close()

        def upload_images():
            static_data = {
                "before": self.static_section_widgets["before"]["entry"].get().strip(),
                "during": self.static_section_widgets["during"]["entry"].get().strip(),
                "after": self.static_section_widgets["after"]["entry"].get().strip(),
                "station_limits": self.static_section_widgets["station_limits"]["entry"].get().strip()
            }
            static_provided = static_data["before"] or static_data["during"] or static_data["after"]
            dynamic_provided = any(
                row["before"].get().strip() or row["during"].get().strip() or row["after"].get().strip()
                for row in self.dynamic_rows_entries
            )
            if not (static_provided or dynamic_provided):
                messagebox.showerror("Error", "Please upload at least one geotagged image.")
                return
            try:
                update_all_uploaded_images(
                    item_number, item_name,
                    static_data=static_data,
                    dynamic_rows=self.dynamic_rows_entries
                )
                messagebox.showinfo("Success", "Images and station limits updated successfully!")
                self.on_add_image_window_close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update images: {e}")

        CTkButton(btn_frame, text="Submit", width=150, command=upload_images).pack(side="left", padx=20, pady=10)
        CTkButton(btn_frame, text="Cancel", width=150, command=self.on_add_image_window_close).pack(side="left", padx=20, pady=10)
        CTkButton(
            btn_frame,
            text="Generate Report",
            width=150,
            command=lambda: self.generate_report(item_number, item_name)
        ).pack(side="left", padx=20, pady=10)

    def on_add_image_window_close(self):
        if self.add_image_window is not None:
            self.add_image_window.destroy()
            self.add_image_window = None

    def close_add_image_window(self):
        if self.add_image_window is not None and self.add_image_window.winfo_exists():
            self.add_image_window.destroy()
            self.add_image_window = None

    def fetch_project_details(self):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("SELECT project_name, location, project_id, contractor_name, project_type FROM project_informations LIMIT 1")
            row = cursor.fetchone()
            return dict(zip(["project_name", "location", "project_id", "contractor_name", "project_type"], row)) if row else {}
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error fetching project details: {e}")
            return {}
        finally:
            conn.close()

    def fetch_selected_construction_items(self):
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            # Modified query to fetch item_number, item_name, quantity, unit
            cursor.execute("""
                SELECT item_number, item_name, quantity, unit
                FROM selected_construction_items
            """)
            return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error fetching construction items: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def generate_report(self, item_number, item_name):
        """
        Generate a Word document report for the given construction item.
        Both the static row (row_index=0) and dynamic rows (row_index>0) that haven't been reported (report_generated=0)
        are combined into a list. For each row, the project information is printed at the top of the page.
        After report generation, the corresponding rows are marked as reported.
        """
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            # Fetch static row if not yet reported.
            cursor.execute("""
                SELECT image_before, image_during, image_after, station_limits, report_generated
                FROM completed_construction_images
                WHERE item_number=? AND item_name=? AND row_index=0 AND report_generated=0
            """, (item_number, item_name))
            static_row = cursor.fetchone()
            
            # Fetch dynamic rows not yet reported.
            cursor.execute("""
                SELECT row_index, image_before, image_during, image_after, station_limits, report_generated
                FROM completed_construction_images
                WHERE item_number=? AND item_name=? AND row_index > 0 AND report_generated=0
            """, (item_number, item_name))
            dynamic_rows = cursor.fetchall()
            
            if not static_row and not dynamic_rows:
                messagebox.showinfo("No New Data", "No new attachments to generate report.")
                return

            # Fetch project information.
            cursor.execute("""
                SELECT project_id, project_name, location, contractor_name
                FROM project_informations
            """)
            project_row = cursor.fetchone()
            if project_row:
                (project_id, project_name, location, contractor_name) = project_row
            else:
                messagebox.showerror("Error", "No project information found.")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch image data: {e}")
            return
        finally:
            conn.close()

        combined_rows = []
        if static_row:
            combined_rows.append(static_row)
        combined_rows.extend(dynamic_rows)

        document = Document()
        document.styles['Normal'].paragraph_format.space_after = Pt(0)
        
        for section in document.sections:
            section.top_margin = Cm(1.27)
            section.bottom_margin = Cm(1.27)
            section.left_margin = Cm(1.27)
            section.right_margin = Cm(1.27)

        # --- Add header with logos and centered text (global header) ---
        section = document.sections[0]
        header = section.header
        available_width = section.page_width - section.left_margin - section.right_margin

        header_table = header.add_table(rows=1, cols=3, width=available_width)
        header_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        left_cell = header_table.cell(0, 0)
        center_cell = header_table.cell(0, 1)
        right_cell = header_table.cell(0, 2)

        set_cell_width(left_cell, 2000)
        set_cell_width(center_cell, 8000)
        set_cell_width(right_cell, 2000)
        
        left_logo_path = resource_path("images/prdp_logo.png")
        
        p_left = left_cell.paragraphs[0]
        p_left.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if os.path.exists(left_logo_path):
            p_left.add_run().add_picture(left_logo_path, width=Inches(1))
        else:
            p_left.add_run("Left Logo")
        
        p_center = center_cell.paragraphs[0]
        p_center.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_center.add_run("Republic of the Philippines\n")
        run = p_center.add_run("PHILIPPINE RURAL DEVELOPMENT PROJECT\n")
        run.bold = True
        p_center.add_run("(Input Province Name)\n")
        run = p_center.add_run("(Input Municipality Name)")
        run.bold = True
        
        right_cell.text = ""
        nested_table = right_cell.add_table(rows=1, cols=1)
        nested_table.style = 'Table Grid'
        nested_cell = nested_table.cell(0, 0)
        p_box = nested_cell.paragraphs[0]
        p_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_box.add_run("Insert Municipality Logo")

        for idx, row in enumerate(combined_rows):
            if idx > 0:
                document.add_page_break()
                
            document.add_paragraph()
            document.add_paragraph()
                    
            p = document.add_paragraph()
            p.add_run("NAME OF PROJECT: ").bold = True
            p.add_run(project_name).bold = True

            p = document.add_paragraph()
            p.add_run("LOCATION: ").bold = True
            p.add_run(location).bold = True

            p = document.add_paragraph()
            p.add_run("PROJECT ID: ").bold = True
            p.add_run(str(project_id)).bold = True

            p = document.add_paragraph()
            p.add_run("CONTRACTOR: ").bold = True
            p.add_run(contractor_name).bold = True
            
            document.add_paragraph()

            p = document.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(f'ITEM {str(item_number).upper()} {item_name.upper()}').bold = True

            if len(row) == 5:
                before_img, during_img, after_img, station_limits, _ = row
            else:
                _, before_img, during_img, after_img, station_limits, _ = row

            if station_limits:
                p_station = document.add_paragraph(f'STATION LIMIT: {station_limits}')
                p_station.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            for phase, img_path in zip(["BEFORE", "DURING", "AFTER"], [before_img, during_img, after_img]):
                p_phase = document.add_paragraph(phase)
                p_phase.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if img_path and os.path.exists(img_path):
                    try:
                        document.add_picture(img_path, width=Inches(4), height=Inches(2))
                        last_paragraph = document.paragraphs[-1]
                        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    except Exception as e:
                        document.add_paragraph("Error adding image.")
                else:
                    document.add_paragraph("No image available.")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Documents", "*.docx")],
            title="Save Report As"
        )
        if file_path:
            try:
                document.save(file_path)
                messagebox.showinfo("Success", f"Report saved as {file_path}")
                conn = sqlite3.connect(self.db_filename)
                cursor = conn.cursor()
                if static_row:
                    cursor.execute("""
                        UPDATE completed_construction_images
                        SET report_generated=1
                        WHERE item_number=? AND item_name=? AND row_index=0
                    """, (item_number, item_name))
                for row in dynamic_rows:
                    row_index = row[0]
                    cursor.execute("""
                        UPDATE completed_construction_images
                        SET report_generated=1
                        WHERE item_number=? AND item_name=? AND row_index=?
                    """, (item_number, item_name, row_index))
                conn.commit()
                conn.close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save document: {e}")

    def on_close(self):
        self.logout()

    def logout(self):
        self.close_add_image_window()
        self.logout_button.configure(state="disabled")
        if self.login_app:
            self.login_app.deiconify()
        self.withdraw()
        self.after(200, self.destroy)
