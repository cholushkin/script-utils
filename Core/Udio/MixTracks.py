# Core/Udio/AddNewTracks.py
import os
import zipfile
import json
import shutil
import importlib.util
from pydub import AudioSegment

# Add Core to path so we can import ConfigManager, LogManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from Core.ConfigManager import ConfigManager
from Core.LogManager import LogManager

class MixTracks:
    def __init__(self, look_folders, log_level="INFO", effects_path="MixTracksImplementation/Effects"):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.look_folders = [os.path.join(self.project_root, folder) for folder in look_folders]
        self.log_level = log_level.upper()
        self.effects_path = os.path.join(self.project_root, effects_path)
        self.effects = self._load_effects()

    def _log(self, level, message):
        levels = {"DEBUG": 1, "INFO": 2, "WARNING": 3, "ERROR": 4}
        if levels.get(level.upper(), 2) >= levels.get(self.log_level, 2):
            print(f"[{level.upper()}] {message}")

    def _find_mix_files(self):
        mix_files = []
        for folder in self.look_folders:
            if not os.path.isdir(folder):
                self._log("WARNING", f"Folder not found: {folder}")
                continue
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(".mix.json"):
                        mix_files.append(os.path.join(root, file))
        return mix_files

    def _load_effects(self):
        effects = {}
        if not os.path.isdir(self.effects_path):
            self._log("WARNING", f"Effects directory not found: {self.effects_path}")
            return effects

        for filename in os.listdir(self.effects_path):
            if filename.endswith(".py") and filename != "__init__.py":
                effect_path = os.path.join(self.effects_path, filename)
                spec = importlib.util.spec_from_file_location("effect_module", effect_path)
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    if hasattr(module, "effect_name") and hasattr(module, "apply_effect"):
                        effects.update({module.effect_name: module.apply_effect})
                    else:
                        self._log("WARNING", f"Effect module {filename} missing 'effect_name' or 'apply_effect'.")
                except Exception as e:
                    self._log("ERROR", f"Error loading effect module {filename}: {e}")
        return effects

    def process_track(self, track_config, config_file_dir):
        if track_config.get("ignore", False):
            self._log("INFO", f"Skipping track {track_config.get('output_file', 'unknown')} (ignored)")
            return

        source_path = os.path.join(config_file_dir, track_config["source_path"])
        output_mp3_path = os.path.join(config_file_dir, track_config["output_file"])
        bitrate = track_config.get("bitrate", "192k")
        temp_folder = source_path.replace(".zip", "_Temp")
        expected_files = ["bass.wav", "drums.wav", "other.wav", "vocals.wav"]
        track_data = {}

        self._log("INFO", f"Processing track from: {source_path}")

        if not os.path.exists(source_path):
            self._log("ERROR", f"ZIP file not found: {source_path}")
            return

        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        # Extract ZIP file
        try:
            with zipfile.ZipFile(source_path, 'r') as zip_ref:
                zip_ref.extractall(temp_folder)
        except zipfile.BadZipFile:
            self._log("ERROR", f"Invalid ZIP file: {source_path}")
            shutil.rmtree(temp_folder, ignore_errors=True)
            return
        except Exception as e:
            self._log("ERROR", f"Error extracting ZIP file {source_path}: {e}")
            shutil.rmtree(temp_folder, ignore_errors=True)
            return

        # Load expected files
        for file in expected_files:
            file_path = os.path.join(temp_folder, file)
            if os.path.exists(file_path):
                try:
                    track_data[file] = AudioSegment.from_wav(file_path)
                except Exception as e:
                    self._log("WARNING", f"Error loading {file} from {source_path}: {e}")
            else:
                self._log("WARNING", f"Missing {file} in {source_path}")

        # Apply effects dynamically
        for effect_name, effect_params in track_config.get("effects", {}).items():
            if effect_name in self.effects:
                target_track = effect_params.get("target_track", None)
                effect_function = self.effects[effect_name]
                effect_params = {k: v for k, v in effect_params.items() if k != "target_track"}

                if target_track and target_track in track_data:
                    self._log("DEBUG", f"Applying {effect_name} to {target_track}")
                    try:
                        track_data[target_track] = effect_function(track_data[target_track], **effect_params)
                    except Exception as e:
                        self._log("ERROR", f"Error applying effect {effect_name} to {target_track}: {e}")
                else:
                    self._log("DEBUG", f"Applying {effect_name} to entire track")
                    for key in track_data:
                        try:
                            track_data[key] = effect_function(track_data[key], **effect_params)
                        except Exception as e:
                            self._log("ERROR", f"Error applying effect {effect_name} to {key}: {e}")
            else:
                self._log("WARNING", f"Effect '{effect_name}' not found.")

        # Merge tracks
        merged_audio = None
        for file in expected_files:
            if file in track_data:
                if merged_audio is None:
                    merged_audio = track_data[file]
                else:
                    merged_audio = merged_audio.overlay(track_data[file])

        # Export final MP3
        if merged_audio:
            self._log("INFO", f"Exporting final MP3: {output_mp3_path} with bitrate {bitrate}")
            try:
                merged_audio.export(output_mp3_path, format="mp3", bitrate=bitrate)
            except Exception as e:
                self._log("ERROR", f"Error exporting MP3 {output_mp3_path}: {e}")
        else:
            self._log("WARNING", f"No audio data to export for {output_mp3_path}")

        # Clean up temporary files
        shutil.rmtree(temp_folder, ignore_errors=True)
        self._log("DEBUG", f"Deleted temp folder: {temp_folder}")

    def run(self):
        mix_files = self._find_mix_files()
        self._log("INFO", f"Found {len(mix_files)} mix configuration files.")
        for mix_file in mix_files:
            try:
                with open(mix_file, "r") as f:
                    track_config = json.load(f)
                config_file_dir = os.path.dirname(mix_file)
                self.process_track(track_config, config_file_dir)
            except FileNotFoundError:
                self._log("ERROR", f"Mix configuration file not found: {mix_file}")
            except json.JSONDecodeError:
                self._log("ERROR", f"Error decoding JSON in: {mix_file}")
            except Exception as e:
                self._log("ERROR", f"An unexpected error occurred while processing {mix_file}: {e}")

        self._log("INFO", "All tracks processed.")

if __name__ == "__main__":
    # Example usage if running this file directly for testing
    processor = MixTrackProcessor(look_folders=["tracks"], log_level="DEBUG")
    processor.run()