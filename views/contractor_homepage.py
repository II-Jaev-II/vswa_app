import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from customtkinter import CTk, CTkButton, CTkFrame, CTkLabel, CTkEntry, CTkCheckBox
from PIL import ImageTk, Image, ExifTags
import os
import shutil
import uuid
import sys
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

DB_FILENAME = (resource_path("database/vswa_db.db"))

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
            CTkLabel(self.info_frame, text=text, font=("Roboto", 12, "bold"), anchor="w").pack(padx=10, pady=2, anchor="w")

        self.extra_frame = CTkFrame(self, corner_radius=10, fg_color="#11151f")
        self.extra_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.extra_label = CTkLabel(self.extra_frame, text="List of Construction Items", font=("Roboto", 16, "bold"))
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

        # Update headers to include a new "Report" column.
        headers = ["Construction Type", "Item Number", "Item Name", "Actions"]
        col_widths = [200, 100, 500, 150, 130, 150]

        header_frame = CTkFrame(self.scrollable_frame, fg_color="black")
        header_frame.grid(row=0, column=0, columnspan=len(headers), sticky="nsew", padx=1, pady=1)

        for col_index, (col_name, col_width) in enumerate(zip(headers, col_widths)):
            col_label = CTkLabel(header_frame, text=col_name, font=("Roboto", 12, "bold"),
                                 width=col_width, height=30, fg_color="gray20")
            col_label.grid(row=0, column=col_index, padx=1, pady=1, sticky="nsew")

        for col_index in range(len(headers)):
            self.scrollable_frame.grid_columnconfigure(col_index, weight=1)

        selected_items = self.fetch_selected_construction_items()

        for row_index, item in enumerate(selected_items, start=1):
            bg_color = "#2E2E2E" if row_index % 2 == 0 else "#1C1C1C"

            row_frame = CTkFrame(self.scrollable_frame, fg_color="black")
            row_frame.grid(row=row_index, column=0, columnspan=len(headers), sticky="nsew", padx=1, pady=1)

            # Use the first 4 columns from the query (Construction Type, Item Number, Item Name, Status)
            for col_index, (value, col_width) in enumerate(zip(item[:4], col_widths[:4])):
                cell_label = CTkLabel(row_frame, text=value, font=("Roboto", 12),
                                      width=col_width, height=30, fg_color=bg_color)
                cell_label.grid(row=0, column=col_index, padx=1, pady=1, sticky="nsew")

            construction_type, item_number, item_name = item[0], item[1], item[2]

            # Button for adding/updating images.
            add_image_button = CTkButton(
                row_frame, text="Add / Update Image", font=("Roboto", 12),
                command=lambda c=construction_type, i=item_number, n=item_name: self.open_add_image_window(c, i, n),
                width=col_widths[4], height=30
            )
            add_image_button.grid(row=0, column=3, padx=1, pady=1, sticky="nsew")

    def open_add_image_window(self, construction_type, item_number, item_name):
        # If an add image window is already open, bring it to the front.
        if self.add_image_window is not None and self.add_image_window.winfo_exists():
            self.add_image_window.lift()
            return

        self.add_image_window = tk.Toplevel()
        self.add_image_window.title(f"Add / Update Image - {construction_type} | {item_number} | {item_name}")
        self.add_image_window.geometry("1600x800")
        self.add_image_window.resizable(False, False)
        self.add_image_window.configure(bg="#11151f")
        self.add_image_window.protocol("WM_DELETE_WINDOW", self.on_add_image_window_close)

        # Center the window on the screen
        self.add_image_window.update_idletasks()
        width, height = 1600, 800
        x = (self.add_image_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.add_image_window.winfo_screenheight() // 2) - (height // 2)
        self.add_image_window.geometry(f"{width}x{height}+{x}+{y}")

        # Create a container for the entire window content and make it scrollable
        container = tk.Frame(self.add_image_window, bg="#11151f")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#11151f", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # This frame holds all of the window content
        self.frame = tk.Frame(canvas, bg="#11151f")
        window_id = canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # Update scroll region when the content changes
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.frame.bind("<Configure>", on_frame_configure)

        # Ensure that the inner frame always matches the width of the canvas
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # Bind mouse wheel scrolling when the cursor is over the canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ------------------ Static Content ------------------
        tk.Label(self.frame, text="Upload Construction Images", font=("Roboto", 14, "bold"),
                 bg="#11151f", fg="white").grid(row=0, column=0, columnspan=4, pady=10)

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
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.jfif")],
            )
            if filename:
                if has_gps_coordinates(filename):
                    set_preview_pic(filename, label, entry)
                else:
                    messagebox.showwarning("Invalid Image", "Please upload a geotagged photo.")

        # Define static sections for Before, During, After, and Station Limits.
        sections = [
            ("Before", tk.Label(self.frame, bg="#11151f"), CTkEntry(self.frame, width=200), CTkButton(self.frame, text="Browse", width=100)),
            ("During", tk.Label(self.frame, bg="#11151f"), CTkEntry(self.frame, width=200), CTkButton(self.frame, text="Browse", width=100)),
            ("After",  tk.Label(self.frame, bg="#11151f"), CTkEntry(self.frame, width=200), CTkButton(self.frame, text="Browse", width=100)),
            ("Station Limit/Grid", None, CTkEntry(self.frame, width=200), None)
        ]

        for i, (title, img_label, path_entry, browse_btn) in enumerate(sections):
            self.frame.columnconfigure(i, weight=1)
            tk.Label(self.frame, text=title, font=("Roboto", 12, "bold"),
                     bg="#11151f", fg="white").grid(row=1, column=i, pady=5, sticky="nswe")
            if img_label is not None:
                img_label.grid(row=2, column=i, pady=5, sticky="nswe")
            path_entry.grid(row=3, column=i, padx=5, pady=5)
            if browse_btn is not None:
                browse_btn.grid(row=4, column=i, padx=5, pady=5)
                browse_btn.configure(command=lambda lbl=img_label, ent=path_entry: select_pic(lbl, ent))

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
                    station_limits TEXT
                )
            """)
            cursor.execute("""
                SELECT image_before, image_during, image_after, station_limits 
                FROM completed_construction_images 
                WHERE construction_type=? AND item_number=? AND item_name=? AND row_index=0
            """, (construction_type, item_number, item_name))
            row = cursor.fetchone()
            conn.close()
            if row:
                if row[0] and os.path.exists(row[0]):
                    set_preview_pic(row[0], sections[0][1], sections[0][2])
                if row[1] and os.path.exists(row[1]):
                    set_preview_pic(row[1], sections[1][1], sections[1][2])
                if row[2] and os.path.exists(row[2]):
                    set_preview_pic(row[2], sections[2][1], sections[2][2])
                if row[3]:
                    sections[3][2].delete(0, tk.END)
                    sections[3][2].insert(0, row[3])
        except Exception as e:
            print(f"Error fetching existing images: {e}")

        # Dynamic rows for additional image entries.
        tk.Frame(self.frame, height=2, bg="gray").grid(row=5, column=0, columnspan=4, pady=10, sticky="ew")
        dynamic_rows_container = tk.Frame(self.frame, bg="#11151f")
        dynamic_rows_container.grid(row=6, column=0, columnspan=4, sticky="ew")
        self.dynamic_rows_entries = []

        def add_new_row(prepopulated_data=None):
            row_frame = tk.Frame(dynamic_rows_container, bg="#11151f", bd=1, relief="solid", highlightthickness=1, highlightbackground="gray")
            row_frame.pack(fill="x", pady=5, padx=5)
            row_entries = {}

            # Add a checkbox to decide if this row should be included in the report.
            include_var = tk.BooleanVar(value=True)  # default checked
            include_checkbox = CTkCheckBox(row_frame, text="Include", variable=include_var)
            include_checkbox.pack(side="left", padx=5, pady=5)
            row_entries["include"] = include_var

            # Create entries for each phase with lowercase keys.
            for phase in ["Before", "During", "After", "Station Limits"]:
                phase_frame = tk.Frame(row_frame, bg="#11151f")
                phase_frame.pack(side="left", expand=True, padx=5, pady=5)
                tk.Label(phase_frame, text=phase, font=("Roboto", 12, "bold"),
                        bg="#11151f", fg="white").pack()
                if phase in ["Before", "During", "After"]:
                    preview_label = tk.Label(phase_frame, bg="#11151f")
                    preview_label.pack(pady=5)
                    path_entry = CTkEntry(phase_frame, width=200)
                    path_entry.pack(pady=5)
                    browse_btn = CTkButton(phase_frame, text="Browse", width=100,
                                        command=lambda lbl=preview_label, ent=path_entry: select_pic(lbl, ent))
                    browse_btn.pack(pady=5)
                    if prepopulated_data and prepopulated_data.get(phase.lower(), ""):
                        file_path = prepopulated_data.get(phase.lower())
                        path_entry.insert(0, file_path)
                        if os.path.exists(file_path):
                            set_preview_pic(file_path, preview_label, path_entry)
                    row_entries[phase.lower()] = path_entry
                else:
                    path_entry = CTkEntry(phase_frame, width=200)
                    path_entry.pack(pady=5)
                    if prepopulated_data and prepopulated_data.get("station_limits", ""):
                        path_entry.insert(0, prepopulated_data.get("station_limits"))
                    row_entries["station_limits"] = path_entry

            # Button to remove this dynamic row.
            def remove_row():
                row_frame.destroy()
                if row_entries in self.dynamic_rows_entries:
                    self.dynamic_rows_entries.remove(row_entries)
            remove_btn = CTkButton(row_frame, text="X", width=30, command=remove_row, fg_color="red", hover_color="darkred")
            remove_btn.pack(side="left", padx=5, pady=5)

            self.dynamic_rows_entries.append(row_entries)

        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT image_before, image_during, image_after, station_limits 
                FROM completed_construction_images 
                WHERE construction_type=? AND item_number=? AND item_name=? AND row_index > 0
            """, (construction_type, item_number, item_name))
            dynamic_rows_data = cursor.fetchall()
            conn.close()
            for data in dynamic_rows_data:
                prepopulated_data = {
                    "before": data[0],
                    "during": data[1],
                    "after": data[2],
                    "station_limits": data[3]
                }
                add_new_row(prepopulated_data=prepopulated_data)
        except Exception as e:
            print("Error loading dynamic rows:", e)

        add_row_btn = CTkButton(self.frame, text="Add Row", width=150, command=add_new_row)
        add_row_btn.grid(row=7, column=0, columnspan=4, pady=10)

        def update_all_uploaded_images(construction_type, item_number, item_name, static_data, dynamic_rows):
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
                    station_limits TEXT
                )
            """)
            
            def process_file(new_file, phase):
                if new_file:
                    target_dir = os.path.join(base_dir, phase.lower())
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
                SELECT image_before, image_during, image_after, station_limits 
                FROM completed_construction_images 
                WHERE construction_type=? AND item_number=? AND item_name=?
            """, (construction_type, item_number, item_name))
            existing_rows = cursor.fetchall()
            
            new_files_set = set()
            for row in new_saved_paths.values():
                for key in ["before", "during", "after"]:
                    path = row.get(key)
                    if path:
                        new_files_set.add(os.path.abspath(path))
            
            for row in existing_rows:
                for file_path in row[:3]:
                    if file_path and os.path.exists(file_path):
                        if os.path.abspath(file_path) not in new_files_set:
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                print(f"Error deleting file {file_path}: {e}")
            
            cursor.execute("""
                DELETE FROM completed_construction_images 
                WHERE construction_type=? AND item_number=? AND item_name=?
            """, (construction_type, item_number, item_name))
            
            cursor.execute("""
                INSERT INTO completed_construction_images 
                (construction_type, item_number, item_name, row_index, image_before, image_during, image_after, station_limits)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (construction_type, item_number, item_name, 0,
                  new_saved_paths["0"]["before"], new_saved_paths["0"]["during"], new_saved_paths["0"]["after"],
                  new_saved_paths["0"]["station_limits"]))
            
            for i in range(1, row_index):
                row_data = new_saved_paths[str(i)]
                cursor.execute("""
                    INSERT INTO completed_construction_images 
                    (construction_type, item_number, item_name, row_index, image_before, image_during, image_after, station_limits)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (construction_type, item_number, item_name, i,
                      row_data["before"], row_data["during"], row_data["after"], row_data["station_limits"]))
            
            conn.commit()
            conn.close()

        def upload_images():
            before_path = sections[0][2].get().strip()
            during_path = sections[1][2].get().strip()
            after_path = sections[2][2].get().strip()
            station_limits_val = sections[3][2].get().strip()

            static_provided = before_path or during_path or after_path or station_limits_val
            dynamic_provided = any(
                row["before"].get().strip() or row["during"].get().strip() or row["after"].get().strip() or row["station_limits"].get().strip()
                for row in self.dynamic_rows_entries
            )
            if not (static_provided or dynamic_provided):
                messagebox.showerror("Error", "Please select at least one image or provide station limits.")
                return

            try:
                static_data = {
                    "before": before_path,
                    "during": during_path,
                    "after": after_path,
                    "station_limits": station_limits_val
                }
                update_all_uploaded_images(
                    construction_type, item_number, item_name,
                    static_data=static_data,
                    dynamic_rows=self.dynamic_rows_entries
                )
                messagebox.showinfo("Success", "Images and station limits updated successfully!")
                self.on_add_image_window_close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update images: {e}")

        btn_frame = tk.Frame(self.frame, bg="#11151f")
        btn_frame.grid(row=8, column=0, columnspan=4, pady=10)

        submit_btn = CTkButton(btn_frame, text="Submit", width=150, command=upload_images)
        submit_btn.pack(side="left", padx=20)

        cancel_btn = CTkButton(btn_frame, text="Cancel", width=150, command=self.on_add_image_window_close)
        cancel_btn.pack(side="left", padx=20)
        
        generate_report_btn = CTkButton(btn_frame, text="Generate Report", width=150, command=lambda: self.generate_report(construction_type, item_number, item_name))
        generate_report_btn.pack(side="left", padx=20)

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
            cursor.execute("""
                SELECT ct.name, sci.item_number, sci.item_name, '', 'Add / Update Image'
                FROM selected_construction_items sci
                JOIN construction_types ct ON sci.construction_type_id = ct.id
            """)
            return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error fetching construction items: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def generate_report(self, construction_type, item_number, item_name):
        """
        Generate a Word document report for the given construction item.
        This function fetches the static images (row_index=0) from the database,
        then iterates over dynamic rows in the open_add_image_window (if any are checked)
        to include their data in the report.
        """
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            # Fetch static image data from completed_construction_images table
            cursor.execute("""
                SELECT image_before, image_during, image_after, station_limits
                FROM completed_construction_images
                WHERE construction_type=? AND item_number=? AND item_name=? AND row_index=0
            """, (construction_type, item_number, item_name))
            row = cursor.fetchone()
            if not row:
                messagebox.showerror("Error", "No static image record found for this item.")
                return
            (before_img, during_img, after_img, station_limits) = row
            
            # Fetch project information from project_informations table (assumed to have only one record)
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

        # Create a new Word document and set margins to 1.27 cm on all sides.
        document = Document()
        document.styles['Normal'].paragraph_format.space_after = Pt(0)
        
        for section in document.sections:
            section.top_margin = Cm(1.27)
            section.bottom_margin = Cm(1.27)
            section.left_margin = Cm(1.27)
            section.right_margin = Cm(1.27)

        # --- Add header with logos and centered text ---
        section = document.sections[0]
        header = section.header

        # Calculate available width from page width minus left and right margins.
        available_width = section.page_width - section.left_margin - section.right_margin

        # Create the header table
        header_table = header.add_table(rows=1, cols=3, width=available_width)
        header_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Get the cells
        left_cell = header_table.cell(0, 0)
        center_cell = header_table.cell(0, 1)
        right_cell = header_table.cell(0, 2)

        # Now set the widths
        set_cell_width(left_cell, 2000)
        set_cell_width(center_cell, 8000)
        set_cell_width(right_cell, 2000)
        
        # Define file paths for logos (update these paths as needed)
        left_logo_path = (resource_path("images/prdp_logo.png"))
        
        # Left cell: add left logo (aligned to left)
        left_cell = header_table.cell(0, 0)
        p_left = left_cell.paragraphs[0]
        p_left.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if os.path.exists(left_logo_path):
            p_left.add_run().add_picture(left_logo_path, width=Inches(1))
        else:
            p_left.add_run("Left Logo")
        
        # Center cell: add header text (centered)
        center_cell = header_table.cell(0, 1)
        p_center = center_cell.paragraphs[0]
        p_center.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_center.add_run("Republic of the Philippines\n")
        run = p_center.add_run("PHILIPPINE RURAL DEVELOPMENT PROJECT\n")
        run.bold = True
        p_center.add_run("(Input Province Name)\n")
        run = p_center.add_run("(Input Municipality Name)")
        run.bold = True
        
        # Right cell: insert a box with text "Insert Municipality Logo"
        right_cell = header_table.cell(0, 2)
        # Clear any existing content
        right_cell.text = ""
        # Add a nested table in the right cell with one cell to serve as the box
        nested_table = right_cell.add_table(rows=1, cols=1)
        # Apply a table style that shows borders
        nested_table.style = 'Table Grid'
        nested_cell = nested_table.cell(0, 0)
        p_box = nested_cell.paragraphs[0]
        p_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_box.add_run("Insert Municipality Logo")
        # -------------------------------------------------

        # Insert 2 blank paragraphs between header and project information.
        document.add_paragraph()
        document.add_paragraph()

        # Add project information
        p = document.add_paragraph()
        p.add_run("NAME OF PROJECT: ")
        p.add_run(project_name).bold = True

        p = document.add_paragraph()
        p.add_run("LOCATION: ")
        p.add_run(location).bold = True

        p = document.add_paragraph()
        p.add_run("PROJECT ID: ")
        p.add_run(str(project_id)).bold = True

        p = document.add_paragraph()
        p.add_run("CONTRACTOR: ")
        p.add_run(contractor_name).bold = True
        
        document.add_paragraph()
        
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f'ITEM {str(item_number).upper()} {item_name.upper()}').bold = True

        if station_limits:
            p_station = document.add_paragraph(f'STATION LIMIT: {station_limits}')
            p_station.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
        document.add_paragraph()            

        # Process static images for each phase
        for phase, img_path in zip(["BEFORE", "DURING", "AFTER"], [before_img, during_img, after_img]):
            heading = document.add_paragraph(phase)
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

            if img_path and os.path.exists(img_path):
                try:
                    document.add_picture(img_path, width=Inches(4), height=Inches(2))
                    last_paragraph = document.paragraphs[-1]
                    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                except Exception as e:
                    error_paragraph = document.add_paragraph("Error adding image.")
                    error_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                no_image_paragraph = document.add_paragraph("No image available.")
                no_image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Include dynamic rows that are checked.
        if hasattr(self, 'dynamic_rows_entries'):
            for idx, row_entries in enumerate(self.dynamic_rows_entries, start=1):
                if "include" in row_entries and row_entries["include"].get():
                    document.add_page_break()
                    document.add_paragraph()
                    document.add_paragraph()

                    p = document.add_paragraph()
                    p.add_run("NAME OF PROJECT: ")
                    p.add_run(project_name).bold = True

                    p = document.add_paragraph()
                    p.add_run("LOCATION: ")
                    p.add_run(location).bold = True

                    p = document.add_paragraph()
                    p.add_run("PROJECT ID: ")
                    p.add_run(str(project_id)).bold = True

                    p = document.add_paragraph()
                    p.add_run("CONTRACTOR: ")
                    p.add_run(contractor_name).bold = True
                    
                    document.add_paragraph()

                    p = document.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run(f'ITEM {str(item_number).upper()} {item_name.upper()}').bold = True

                    station_limits_text = row_entries["station_limits"].get().strip()
                    if station_limits_text:
                        p_station = document.add_paragraph(f'STATION LIMIT: {station_limits_text}')
                        p_station.alignment = WD_ALIGN_PARAGRAPH.RIGHT

                    # Process dynamic rows using lowercase keys.
                    for phase in ["before", "during", "after"]:
                        p_phase = document.add_paragraph(phase.upper())
                        p_phase.alignment = WD_ALIGN_PARAGRAPH.CENTER

                        if phase in row_entries:
                            file_path = row_entries[phase].get().strip()
                            if file_path and os.path.exists(file_path):
                                try:
                                    document.add_picture(file_path, width=Inches(4), height=Inches(2))
                                    last_paragraph = document.paragraphs[-1]
                                    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                except Exception as e:
                                    document.add_paragraph("Error adding image.")
                            else:
                                document.add_paragraph("No image available.")
                        else:
                            document.add_paragraph(f"No image entry for {phase} phase.")

        file_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Documents", "*.docx")],
            title="Save Report As"
        )
        if file_path:
            try:
                document.save(file_path)
                messagebox.showinfo("Success", f"Report saved as {file_path}")
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
