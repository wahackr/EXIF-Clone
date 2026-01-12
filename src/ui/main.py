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
        self.geometry("500x400")

        # --- UI Layout (The "View") ---
        self.label = ctk.CTkLabel(self, text="Step 1: Select Source Photo (with GPS)")
        self.label.pack(pady=10)

        self.btn_source = ctk.CTkButton(
            self, text="Choose Source", command=self.select_source
        )
        self.btn_source.pack(pady=5)

        self.btn_targets = ctk.CTkButton(
            self, text="Choose Targets", command=self.select_targets
        )
        self.btn_targets.pack(pady=5)

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

        # Call business logic
        self.label.configure(text=f"Processing {len(self.target_files)} files...")
        results = libs.transfer_gps_data(self.source_path, self.target_files)

        # Update UI with results
        self.label.configure(text=results["message"])
