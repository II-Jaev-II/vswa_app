import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from customtkinter import CTk, CTkButton, CTkFrame, CTkLabel, CTkEntry
from PIL import ImageTk, Image, ExifTags
import os
import shutil
import uuid  # To generate unique file names

DB_FILENAME = "vswa_db.db"

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

        headers = ["Construction Type", "Item Number", "Item Name", "Status", "Actions"]
        col_widths = [200, 100, 500, 150, 130]

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

            # Display the item details
            for col_index, (value, col_width) in enumerate(zip(item[:-1], col_widths[:-1])):
                cell_label = CTkLabel(row_frame, text=value, font=("Roboto", 12),
                                      width=col_width, height=30, fg_color=bg_color)
                cell_label.grid(row=0, column=col_index, padx=1, pady=1, sticky="nsew")

            construction_type, item_number, item_name = item[:3]

            add_image_button = CTkButton(
                row_frame, text="Add / Update Image", font=("Roboto", 12),
                command=lambda c=construction_type, i=item_number, n=item_name: self.open_add_image_window(c, i, n),
                width=col_widths[-1], height=30
            )
            add_image_button.grid(row=0, column=len(headers) - 1, padx=1, pady=1, sticky="nsew")

            for col_index in range(len(headers)):
                row_frame.grid_columnconfigure(col_index, weight=1)

    def open_add_image_window(self, construction_type, item_number, item_name):
        # If an add image window is already open, bring it to the front.
        if self.add_image_window is not None and self.add_image_window.winfo_exists():
            self.add_image_window.lift()
            return

        self.add_image_window = tk.Toplevel()
        self.add_image_window.title(f"Add / Update Image - {construction_type} | {item_number} | {item_name}")
        self.add_image_window.geometry("1400x600")
        self.add_image_window.resizable(False, False)
        self.add_image_window.configure(bg="#11151f")
        self.add_image_window.protocol("WM_DELETE_WINDOW", self.on_add_image_window_close)

        # Center the window on the screen
        self.add_image_window.update_idletasks()
        width, height = 1200, 600
        x = (self.add_image_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.add_image_window.winfo_screenheight() // 2) - (height // 2)
        self.add_image_window.geometry(f"{width}x{height}+{x}+{y}")

        # Create frame for window content
        self.frame = tk.Frame(self.add_image_window, bg="#11151f")
        self.frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Title Label
        tk.Label(self.frame, text="Upload Construction Images", font=("Roboto", 14, "bold"), bg="#11151f", fg="white")\
            .grid(row=0, column=0, columnspan=3, pady=10)
        
        # Helper function to check if the image has GPS coordinates
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

        # Helper function to set a preview image and update its file path entry
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

        # Helper function to let user select an image file
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

        # Define sections for Before, During, and After images
        sections = [
            ("Before", tk.Label(self.frame, bg="#11151f"), CTkEntry(self.frame, width=200), CTkButton(self.frame, text="Browse", width=100)),
            ("During", tk.Label(self.frame, bg="#11151f"), CTkEntry(self.frame, width=200), CTkButton(self.frame, text="Browse", width=100)),
            ("After",  tk.Label(self.frame, bg="#11151f"), CTkEntry(self.frame, width=200), CTkButton(self.frame, text="Browse", width=100)),
        ]

        for i, (title, img_label, path_entry, browse_btn) in enumerate(sections):
            self.frame.columnconfigure(i, weight=1)
            tk.Label(self.frame, text=title, font=("Roboto", 12, "bold"), bg="#11151f", fg="white")\
                .grid(row=1, column=i, pady=5, sticky="nswe")
            img_label.grid(row=2, column=i, pady=5, sticky="nswe")
            path_entry.grid(row=3, column=i, padx=5, pady=5)
            browse_btn.grid(row=4, column=i, padx=5, pady=5)
            browse_btn.configure(command=lambda lbl=img_label, ent=path_entry: select_pic(lbl, ent))

        # If a record exists in the database, fetch and display the existing images.
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT image_before, image_during, image_after 
                FROM completed_construction_images 
                WHERE construction_type=? AND item_number=? AND item_name=?
            """, (construction_type, item_number, item_name))
            row = cursor.fetchone()
            conn.close()
            if row:
                # row[0]: Before, row[1]: During, row[2]: After
                if row[0] and os.path.exists(row[0]):
                    set_preview_pic(row[0], sections[0][1], sections[0][2])
                if row[1] and os.path.exists(row[1]):
                    set_preview_pic(row[1], sections[1][1], sections[1][2])
                if row[2] and os.path.exists(row[2]):
                    set_preview_pic(row[2], sections[2][1], sections[2][2])
        except Exception as e:
            print(f"Error fetching existing images: {e}")

        # Horizontal separator
        tk.Frame(self.frame, height=2, bg="gray").grid(row=5, column=0, columnspan=3, pady=10, sticky="ew")

        # Function to update (or insert) images for the construction item.
        def update_uploaded_images(construction_type, item_number, item_name, before_path, during_path, after_path):
            base_dir = "images"  # Base folder for images
            phases = {"before": before_path, "during": during_path, "after": after_path}
            new_saved_paths = {"before": None, "during": None, "after": None}

            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            # Fetch current image paths for this item.
            cursor.execute("""
                SELECT image_before, image_during, image_after 
                FROM completed_construction_images 
                WHERE construction_type=? AND item_number=? AND item_name=?
            """, (construction_type, item_number, item_name))
            row = cursor.fetchone()
            current_paths = {"before": None, "during": None, "after": None}
            if row:
                current_paths["before"], current_paths["during"], current_paths["after"] = row

            # Process each phase.
            for phase, new_file in phases.items():
                if new_file:
                    # If the new file is the same as the current one, skip copying/deleting.
                    if current_paths[phase] and os.path.abspath(new_file) == os.path.abspath(current_paths[phase]):
                        new_saved_paths[phase] = current_paths[phase]
                        continue

                    # Check if the source file exists.
                    if not os.path.exists(new_file):
                        raise FileNotFoundError(f"Source file not found: {new_file}")
                    target_dir = os.path.join(base_dir, phase)
                    os.makedirs(target_dir, exist_ok=True)
                    original_filename = os.path.basename(new_file)
                    # Generate a unique file name to avoid collisions.
                    unique_filename = f"{os.path.splitext(original_filename)[0]}_{uuid.uuid4().hex}{os.path.splitext(original_filename)[1]}"
                    target_path = os.path.join(target_dir, unique_filename)
                    
                    # If an old image exists and is different from the new one, delete it.
                    if current_paths[phase] and os.path.exists(current_paths[phase]):
                        try:
                            os.remove(current_paths[phase])
                        except Exception as e:
                            print(f"Error deleting file {current_paths[phase]}: {e}")
                    # Copy the new image using the unique file name.
                    shutil.copy(new_file, target_path)
                    new_saved_paths[phase] = target_path
                else:
                    # Retain the current image if no new file is provided.
                    new_saved_paths[phase] = current_paths[phase]

            # If a record exists, update it; otherwise, insert a new one.
            if row:
                cursor.execute("""
                    UPDATE completed_construction_images 
                    SET image_before=?, image_during=?, image_after=?
                    WHERE construction_type=? AND item_number=? AND item_name=?
                """, (new_saved_paths["before"], new_saved_paths["during"], new_saved_paths["after"],
                    construction_type, item_number, item_name))
            else:
                cursor.execute("""
                    INSERT INTO completed_construction_images 
                    (construction_type, item_number, item_name, image_before, image_during, image_after)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (construction_type, item_number, item_name,
                    new_saved_paths["before"], new_saved_paths["during"], new_saved_paths["after"]))
            conn.commit()
            conn.close()

        # Function called when Submit is clicked.
        def upload_images():
            before_path = sections[0][2].get().strip()
            during_path = sections[1][2].get().strip()
            after_path = sections[2][2].get().strip()

            if not (before_path or during_path or after_path):
                messagebox.showerror("Error", "Please select at least one image.")
                return

            try:
                update_uploaded_images(construction_type, item_number, item_name,
                                       before_path, during_path, after_path)
                messagebox.showinfo("Success", "Images updated successfully!")
                self.on_add_image_window_close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update images: {e}")

        # Submit & Cancel Buttons
        btn_frame = tk.Frame(self.frame, bg="#11151f")
        btn_frame.grid(row=6, column=0, columnspan=3, pady=10)

        submit_btn = CTkButton(btn_frame, text="Submit", width=150, command=upload_images)
        submit_btn.pack(side="left", padx=20)

        cancel_btn = CTkButton(btn_frame, text="Cancel", width=150, command=self.on_add_image_window_close)
        cancel_btn.pack(side="left", padx=20)

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

    def on_close(self):
        self.logout()

    def logout(self):
        self.close_add_image_window()
        self.logout_button.configure(state="disabled")
        if self.login_app:
            self.login_app.deiconify()
        self.withdraw()
        self.after(200, self.destroy)