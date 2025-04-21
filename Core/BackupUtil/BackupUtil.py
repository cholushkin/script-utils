import os
import zipfile
import time
from datetime import datetime
from fnmatch import fnmatch
import sys

# Add Core to path so we can import ConfigManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from Core.ConfigManager import ConfigManager

class BackupUtil:
    def __init__(self, destination_path, folders, excludes=None):
        # Correcting the project root
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.destination_path = destination_path
        self.folders = [os.path.join(self.project_root, folder) for folder in folders]  # Correct the folder paths
        self.excludes = excludes or []

        # Replace {DATE} in destination path
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.destination_zip = os.path.abspath(destination_path.replace("{DATE}", current_date))
        self.compression_level = zipfile.ZIP_DEFLATED

        # Load config
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.log_level = self.config.get("log_level", "balanced")

        if self.log_level == "maximum":
            print("=== BackupUtil Initialized ===")
            print("Project root:", self.project_root)
            print("Folders to backup:")
            for folder in self.folders:
                print(" →", folder)
            print("Exclude patterns:", self.excludes)
            print("Destination zip path:", self.destination_zip)
            print("Compression level: ZIP_DEFLATED")

    def is_excluded(self, filepath):
        rel_path = os.path.relpath(filepath, self.project_root)
        result = any(fnmatch(rel_path, pattern) for pattern in self.excludes)
        if self.log_level == "maximum" and result:
            print(f"Excluded by pattern: {rel_path}")
        return result

    def get_next_filename(self, filename):
        base, ext = os.path.splitext(filename)
        counter = 2
        new_filename = f"{base} ({counter}){ext}"
        while os.path.exists(new_filename):
            counter += 1
            new_filename = f"{base} ({counter}){ext}"
        if self.log_level != "minimum":
            print(f"Existing backup found. New name: {new_filename}")
        return new_filename

    def backup(self):
        start_time = time.time()
        if self.log_level != "minimum":
            print("Starting backup...")

        # Check if the folders exist
        for folder in self.folders:
            if not os.path.exists(folder):
                print(f"Error: Folder not found - {folder}")

        if os.path.exists(self.destination_zip):
            if self.log_level != "minimum":
                print(f"{self.destination_zip} already exists.")
            self.destination_zip = self.get_next_filename(self.destination_zip)

        os.makedirs(os.path.dirname(self.destination_zip), exist_ok=True)
        if self.log_level != "minimum":
            print(f"Creating archive: {self.destination_zip}")

        total_files = 0
        with zipfile.ZipFile(self.destination_zip, 'w', self.compression_level) as zipf:
            for folder in self.folders:
                if not os.path.exists(folder):
                    if self.log_level != "minimum":
                        print(f"Warning: Folder not found - {folder}")
                    continue
                for root, dirs, files in os.walk(folder):
                    if self.log_level == "maximum":
                        print(f"Scanning directory: {root}")
                    for file in files:
                        full_path = os.path.join(root, file)
                        if not os.path.exists(full_path):
                            if self.log_level == "maximum":
                                print(f"Skipped non-existent: {full_path}")
                            continue
                        if self.is_excluded(full_path):
                            continue
                        arcname = os.path.relpath(full_path, self.project_root)
                        zipf.write(full_path, arcname)
                        total_files += 1
                        if self.log_level == "maximum":
                            print(f"Added: {arcname}")

        duration = time.time() - start_time
        if self.log_level != "minimum":
            print(f"Backup complete: {self.destination_zip}")
            print(f"Files added: {total_files}")
            print(f"Duration: {duration:.2f} seconds")

    def run(self):
        self.backup()
