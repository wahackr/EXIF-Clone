import threading
import webbrowser
from tkinter import filedialog

import customtkinter as ctk

from libs import main as libs


class ExifTransferApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # --- State Management ---
        self.source_path = None
        self.target_files = []

        # --- Window Configuration ---
        self.title("GPS Metadata Transfer")
        self.geometry("500x600")

        # --- UI Layout (The "View") ---
        self.label = ctk.CTkLabel(self, text="Step 1: Select Source Photo (with GPS)")
        self.label.pack(pady=10)

        self.btn_source = ctk.CTkButton(
            self, text="Choose Source", command=self.select_source
        )
        self.btn_source.pack(pady=5)

        # Location preview label (initially hidden)
        self.location_label = ctk.CTkLabel(self, text="", text_color="blue", cursor="hand2")
        self.location_label.pack(pady=5)
        self.location_label.pack_forget()  # Hide initially

        self.btn_targets = ctk.CTkButton(
            self, text="Choose Targets", command=self.select_targets
        )
        self.btn_targets.pack(pady=5)

        # --- Options Frame ---
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(
            self.options_frame, text="Options:", font=("Arial", 12, "bold")
        ).pack(pady=(10, 5))

        self.copy_date_var = ctk.BooleanVar(value=True)
        self.copy_date_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Copy creation date from source",
            variable=self.copy_date_var,
        )
        self.copy_date_checkbox.pack(pady=5, padx=10, anchor="w")

        self.overwrite_gps_var = ctk.BooleanVar(value=True)
        self.overwrite_gps_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Overwrite GPS if target already has it",
            variable=self.overwrite_gps_var,
        )
        self.overwrite_gps_checkbox.pack(pady=5, padx=10, anchor="w")

        # --- Progress Bar ---
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_bar.set(0)
        self.progress_label = ctk.CTkLabel(self, text="")
        self.progress_label.pack(pady=5)

        self.btn_run = ctk.CTkButton(
            self, text="Transfer GPS Data", fg_color="green", command=self.process_files
        )
        self.btn_run.pack(pady=20)

    def select_source(self):
        """Handle source file selection (UI layer)"""
        file_path = filedialog.askopenfilename(
            title="Select Source Photo",
            filetypes=[
                (
                    "Image files",
                    "*.jpg *.jpeg *.png *.tiff *.heic *.heif *.JPG *.JPEG *.PNG *.TIFF *.HEIC *.HEIF",
                ),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.source_path = file_path
            self.label.configure(text=f"Source: {file_path}")
            
            # Try to extract GPS coordinates
            gps_info = libs.extract_gps_coordinates(file_path)
            if gps_info:
                # Display location preview link
                self.location_label.configure(
                    text=f"📍 Location: {gps_info['latitude']:.5f}, {gps_info['longitude']:.5f} (Click to view on map)"
                )
                self.location_label.pack(pady=5)
                # Bind click event to open Google Maps
                self.location_label.bind("<Button-1>", lambda e: self._open_maps_url(gps_info['maps_url']))
            else:
                # Hide location label if no GPS data
                self.location_label.pack_forget()

    def _open_maps_url(self, url):
        """Open Google Maps URL in default browser"""
        webbrowser.open(url)

    def select_targets(self):
        """Handle target files selection (UI layer)"""
        file_paths = filedialog.askopenfilenames(
            title="Select Target Photos",
            filetypes=[
                (
                    "Image files",
                    "*.jpg *.jpeg *.png *.heic *.heif *.JPG *.JPEG *.PNG *.HEIC *.HEIF",
                )
            ],
        )
        if file_paths:
            self.target_files = list(file_paths)
            self.label.configure(text=f"Selected {len(file_paths)} target file(s)")

    def process_files(self):
        """Process files by calling business logic (UI layer coordinates)"""
        # Validate inputs
        if not self.source_path:
            self.label.configure(text="Error: Please select a source photo first!")
            return

        if not self.target_files:
            self.label.configure(text="Error: Please select target photos!")
            return

        # Get option values
        options = {
            "copy_date": self.copy_date_var.get(),
            "overwrite_gps": self.overwrite_gps_var.get(),
        }

        # Disable button during processing
        self.btn_run.configure(state="disabled")

        # Reset progress
        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.label.configure(text=f"Processing {len(self.target_files)} files...")

        # Run processing in background thread to keep UI responsive
        thread = threading.Thread(
            target=self._process_in_background,
            args=(self.source_path, self.target_files, options),
            daemon=True,
        )
        thread.start()

    def _process_in_background(self, source_path, target_files, options):
        """Run business logic in background thread"""
        total = len(target_files)

        # Process files one at a time and update UI after each
        results = libs.transfer_gps_data_batch(
            source_path,
            target_files,
            options,
            progress_callback=lambda idx, total, status: self.after(
                0, self.update_progress, idx, total, status
            ),
        )

        # Update UI with final results (must use after() for thread safety)
        self.after(0, self._finish_processing, results)

    def _finish_processing(self, results):
        """Update UI with final results (called from main thread)"""
        self.label.configure(text=results["message"])
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Complete!")
        self.btn_run.configure(state="normal")

    def update_progress(self, current, total, status=""):
        """Update progress bar and label (called from main thread)"""
        progress = current / total if total > 0 else 0
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Processing: {current}/{total} {status}")
