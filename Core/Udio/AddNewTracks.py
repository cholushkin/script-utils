import os
import shutil
import re
import sys
from collections import defaultdict

# Add Core to path so we can import ConfigManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from Core.ConfigManager import ConfigManager

class AddNewTracks:
    """
    Moves or copies MP3 and ZIP file pairs into organized subfolders, handling naming and error conditions.
    All paths are relative to the UserProject root, which is calculated automatically.
    """
    def __init__(self, source_directory, track_target_path, move_files=True):
        """
        Initializes the AddNewTrack object.

        Args:
            source_directory (str): The path to the directory containing the MP3 and ZIP files,
                                     relative to the project root.
            track_target_path (str): The path to the target directory *relative* to the UserProject root
                                     where track subfolders will be created (e.g., "tracks").
            move_files (bool, optional): If True, files are moved; if False, files are copied. Defaults to True.
        """
        # Calculate project root dynamically
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.source_path = os.path.join(self.project_root, source_directory)  # Make source_path absolute
        self.track_target_path = os.path.join(self.project_root, track_target_path)
        self.move_files = move_files
        self.files_processed_count = 0
        self.folders_created_count = 0
        self.logs = []
        self.action_word = "Moved" if move_files else "Copied"
        self.file_operation = shutil.move if move_files else shutil.copy2
        self.count_description = "Files moved" if move_files else "Files copied"

        # Load config
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.log_level = self.config.get("log_level", "balanced")

    def log(self, message):
        """Adds a message to the log, respecting the current log level."""
        if self.log_level == "maximum":
            self.logs.append(message)
            print(message)  # Print always in maximum
        elif self.log_level == "balanced":
            self.logs.append(message)
            # Print messages selectively (e.g., errors, warnings, key actions)
            if "Error" in message or "Warning" in message or "Created" in message or "Moved" in message or "Copied" in message:
                print(message)
        elif self.log_level == "minimum":
            self.logs.append(message)
            if "Error" in message:
                print(message)

    def ensure_target_root_exists(self):
        """Ensures that the target root directory exists."""
        if not os.path.isdir(self.track_target_path):
            try:
                os.makedirs(self.track_target_path)
                self.log(f"📁 Created target root directory: {self.track_target_path}")
                self.folders_created_count += 1
            except OSError as e:
                self.log(f"❌ Error: Could not create target root directory '{self.track_target_path}'. {e}")
                return False
        return True

    def get_source_files(self):
        """
        Gets all files from the source directory and performs initial validation.
        """
        try:
            all_items = os.listdir(self.source_path)
            source_files = [f for f in all_items if os.path.isfile(os.path.join(self.source_path, f))]
        except OSError as e:
            self.log(f"❌ Error: Could not read source directory '{self.source_path}'. {e}")
            return None, None, None, None

        mp3_files = set()
        zip_files = set()
        basenames_mp3 = set()
        basenames_zip = set()

        for f in source_files:
            name, ext = os.path.splitext(f)
            ext_lower = ext.lower()
            if ext_lower == ".mp3":
                mp3_files.add(f)
                basenames_mp3.add(name)
            elif ext_lower == ".zip":
                zip_files.add(f)
                basenames_zip.add(name)
        return mp3_files, zip_files, basenames_mp3, basenames_zip

    def validate_file_pairs(self, basenames_mp3, basenames_zip):
        """Validates that there is a matching .mp3 and .zip file for each base name."""
        inconsistent_basenames = basenames_mp3.symmetric_difference(basenames_zip)

        if inconsistent_basenames:
            self.log("❌ Error: File inconsistency detected. Found '.mp3' without matching '.zip' or vice-versa.")
            self.log("Inconsistent base names:")
            for base in inconsistent_basenames:
                if base in basenames_mp3:
                    self.log(f"  - Found '{base}.mp3' without matching '.zip'")
                else:
                    self.log(f"  - Found '{base}.zip' without matching '.mp3'")
            return None

        return basenames_mp3.intersection(basenames_zip)

    def process_files(self, valid_basenames):
        """Processes the valid MP3/ZIP file pairs."""
        if not valid_basenames:
            self.log("ℹ️ No MP3/ZIP pairs found in the source directory.")
            return

        self.log(f"ℹ️ Found {len(valid_basenames)} valid MP3/ZIP pairs for processing.")

        sorted_basenames = sorted(list(valid_basenames))

        for base_name_extless in sorted_basenames:
            source_mp3 = base_name_extless + ".mp3"
            source_zip = base_name_extless + ".zip"

            source_mp3_full_path = os.path.join(self.source_path, source_mp3)
            source_zip_full_path = os.path.join(self.source_path, source_zip)

            # Double check
            if not os.path.exists(source_mp3_full_path) or not os.path.exists(source_zip_full_path):
                self.log(f"⚠️ Warning: Source file(s) for '{base_name_extless}' disappeared before processing. Skipping.")
                continue

            # Determine subfolder name
            match = re.match(r"^(.*?)(?: \(\d+\))?$", base_name_extless)
            folder_name = match.group(1).strip() if match else base_name_extless.strip()
            dest_folder_path = os.path.join(self.track_target_path, folder_name)
            relative_dest_folder = os.path.join(folder_name)

            # Create subfolder
            if not os.path.isdir(dest_folder_path):
                try:
                    os.makedirs(dest_folder_path)
                    self.log(f"📁 Subfolder created: {relative_dest_folder}")
                    self.folders_created_count += 1
                except OSError as e:
                    self.log(f"❌ Error: Could not create subfolder '{dest_folder_path}'. Skipping '{base_name_extless}'. {e}")
                    continue

            # Determine next number
            next_number = 1
            try:
                existing_files = os.listdir(dest_folder_path)
                max_num = 0
                pattern = re.compile(r"^" + re.escape(folder_name) + r" (\d+)\.(mp3|zip)$", re.IGNORECASE)
                for fname in existing_files:
                    file_match = pattern.match(fname)
                    if file_match:
                        num = int(file_match.group(1))
                        if num > max_num:
                            max_num = num
                next_number = max_num + 1
            except OSError as e:
                self.log(f"❌ Error: Could not read destination subfolder '{dest_folder_path}'. Skipping '{base_name_extless}'. {e}")
                continue

            # Construct new paths
            new_mp3_name = f"{folder_name} {next_number}.mp3"
            new_zip_name = f"{folder_name} {next_number}.zip"
            dest_mp3_path = os.path.join(dest_folder_path, new_mp3_name)
            dest_zip_path = os.path.join(dest_folder_path, new_zip_name)

            # Process files
            try:
                # --- Process MP3 file ---
                self.file_operation(source_mp3_full_path, dest_mp3_path)
                log_dest_mp3 = os.path.join(relative_dest_folder, new_mp3_name)
                self.log(f"➡️ {self.action_word} {source_mp3} to {log_dest_mp3}")
                self.files_processed_count += 1

                try:
                    # --- Process ZIP file ---
                    if not os.path.exists(source_zip_full_path):
                        self.log(f"❌ Error: Source ZIP '{source_zip}' disappeared before it could be {self.action_word.lower()}. MP3 was already {self.action_word.lower()}.")
                        if not self.move_files and os.path.exists(dest_mp3_path):
                            try:
                                os.remove(dest_mp3_path)
                                self.log(f"🧹 Cleaned up partially {self.action_word.lower()} file: {log_dest_mp3}")
                                self.files_processed_count -= 1
                            except OSError as e_rem:
                                self.log(f"⚠️ Warning: Could not clean up partially {self.action_word.lower()} MP3 '{log_dest_mp3}'. {e_rem}")
                    else:
                        self.file_operation(source_zip_full_path, dest_zip_path)
                        log_dest_zip = os.path.join(relative_dest_folder, new_zip_name)
                        self.log(f"➡️ {self.action_word} {source_zip} to {log_dest_zip}")
                        self.files_processed_count += 1

                except Exception as e_zip:
                    self.log(f"❌ Error: Failed to {self.action_word.lower()} ZIP file '{source_zip}' after {self.action_word.lower()}ing MP3. {e_zip}")
                    if not self.move_files and os.path.exists(dest_mp3_path):
                        try:
                            os.remove(dest_mp3_path)
                            self.log(f"🧹 Cleaned up partially {self.action_word.lower()} file: {log_dest_mp3}")
                            self.files_processed_count -= 1
                        except OSError as e_rem:
                            self.log(f"⚠️ Warning: Could not clean up partially {self.action_word.lower()} MP3 '{log_dest_mp3}'. {e_rem}")

            except Exception as e_mp3:
                self.log(f"❌ Error: Failed to {self.action_word.lower()} MP3 file '{source_mp3}'. Skipping pair. {e_mp3}")

    def run(self):
        """Runs the AddNewTrack process."""
        self.log(f"ℹ️ Source directory: {self.source_path}")
        self.log(f"ℹ️ Target root directory: {self.track_target_path}")
        self.log(f"ℹ️ Mode: {'Move files' if self.move_files else 'Copy files'}")
        self.log("-" * 30)

        if not self.ensure_target_root_exists():
            sys.exit(1)

        mp3_files, zip_files, basenames_mp3, basenames_zip = self.get_source_files()
        if (mp3_files, zip_files, basenames_mp3, basenames_zip) == (None, None, None, None):
            sys.exit(1)

        valid_basenames = self.validate_file_pairs(basenames_mp3, basenames_zip)
        if valid_basenames is None:
            sys.exit(1)

        self.process_files(valid_basenames)

        self.log("-" * 30)
        self.log("✅ Processing complete.")
        self.log("📊 Summary:")
        self.log(f"  ✅ {self.count_description}: {self.files_processed_count}")
        self.log(f"  ✅ Subfolders created: {self.folders_created_count}")
 