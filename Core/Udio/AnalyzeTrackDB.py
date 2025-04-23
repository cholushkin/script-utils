import os
import json
import hashlib
import time
from mutagen.mp3 import MP3
from pydub import AudioSegment

class AnalyzeTrackDB:
    def __init__(self, look_folders, output_json, output_txt, estimate_bitrates, detect_abrupt_end=False):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # project root
        self.output_json = os.path.join(self.project_root, output_json)
        self.output_txt = os.path.join(self.project_root, output_txt)
        self.look_folders = [os.path.join(self.project_root, folder) for folder in look_folders]
        self.estimate_bitrates = estimate_bitrates
        self.detect_abrupt_end = detect_abrupt_end
        self.logs = []
        self.track_data = []

    def log(self, message):
        self.logs.append(message)

    def write_log_file(self):
        os.makedirs(os.path.dirname(self.output_txt), exist_ok=True)
        with open(self.output_txt, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.logs))

    def get_mp3_duration(self, file_path):
        try:
            audio = MP3(file_path)
            duration = int(audio.info.length)
            minutes = duration // 60
            seconds = duration % 60
            return duration, f"{minutes}:{seconds:02d}"
        except Exception:
            return 0, "Unknown"

    def detect_abrupt_end(self, file_path, threshold_db=-20, check_duration_ms=300):
        try:
            audio = AudioSegment.from_mp3(file_path)
            if len(audio) < check_duration_ms:
                return False
            last_part = audio[-check_duration_ms:]
            return last_part.dBFS > threshold_db
        except Exception:
            return False

    def read_track_metadata(self, txt_file):
        metadata = {"energy": None, "mood": None, "pop": None, "stars": None}
        if os.path.exists(txt_file):
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) == 2:
                            key, value = parts
                            if key in metadata:
                                metadata[key] = float(value)
            except Exception as e:
                self.log(f"Error reading {txt_file}: {e}")
        return metadata

    def estimate_size(self, total_duration):
        sizes = {}
        for bitrate in self.estimate_bitrates:
            kbps = int(bitrate.replace("k", ""))
            mb = (total_duration * kbps / 8) / 1024
            sizes[bitrate] = mb
        return sizes

    def run(self):
        start_time = time.time()

        total_size = 0
        total_duration = 0
        mp3_count = 0
        abrupt_end_count = 0
        md5_hashes = {}
        name_duplicates = {}

        self.log("🔍 Searching for MP3 files...\n")

        for folder in self.look_folders:
            if not os.path.isdir(folder):
                self.log(f"⚠️ Folder not found: {folder}")
                continue

            self.log(f"📂 Searching in: {folder}")
            for root, _, files in os.walk(folder):
                for file in files:
                    if not file.lower().endswith(".mp3"):
                        continue

                    file_path = os.path.join(root, file)
                    txt_file = os.path.splitext(file_path)[0] + ".txt"
                    mix_file = os.path.splitext(file_path)[0] + ".mix.json"
                    file_name = os.path.splitext(file)[0]
                    has_mix = os.path.exists(mix_file)
                    mix_emoji = " 🎛️" if has_mix else ""

                    metadata = self.read_track_metadata(txt_file)
                    energy = metadata["energy"]
                    mood = metadata["mood"]
                    pop = metadata["pop"]
                    stars = metadata["stars"]

                    duration_seconds, duration_str = self.get_mp3_duration(file_path)

                    abrupt_warning = ""
                    if self.detect_abrupt_end:
                        abrupt = self.detect_abrupt_end(file_path)
                        if abrupt:
                            abrupt_warning = "🚨"
                            abrupt_end_count += 1

                    md5 = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                    md5_hashes.setdefault(md5, []).append(file_path)
                    name_duplicates.setdefault(file, []).append(file_path)

                    # Format and log metadata
                    line = f"🎵 {file} [{duration_str}] {abrupt_warning}{mix_emoji}"
                    if energy is not None: line += f" 🔥:{energy:.1f}"
                    if mood is not None:   line += f" 😊:{mood:.1f}"
                    if pop is not None:    line += f" 🎵:{pop:.1f}"
                    if stars is not None:  line += f" ✨:{int(stars)}"

                    self.log(line)

                    self.track_data.append({
                        "name": file_name,
                        "stars": int(stars) if stars is not None else None,
                        "mood": mood,
                        "energy": energy,
                        "pop": pop,
                    })

                    total_size += os.path.getsize(file_path)
                    total_duration += duration_seconds
                    mp3_count += 1

        self.log(f"\n💾 Saving meta file: {self.output_json}")
        with open(self.output_json, "w", encoding="utf-8") as json_file:
            json.dump(self.track_data, json_file, indent=4, ensure_ascii=False)

        self.log("\n=== Summary ===")
        self.log(f"🎼 Total MP3 files found: {mp3_count}")
        self.log(f"💾 Total Space Occupied: {total_size / (1024 * 1024):.2f} MB")
        self.log(f"⏱️ Total Duration: {total_duration // 3600:02d}:{(total_duration % 3600) // 60:02d}:{total_duration % 60:02d}")

        self.log("\n📏 Estimated Total Size at Different Bitrates:")
        for bitrate, size in self.estimate_size(total_duration).items():
            self.log(f"📡 {bitrate}: {size:.2f} MB")

        md5_duplicates = [v for v in md5_hashes.values() if len(v) > 1]
        name_duplicates_filtered = [v for v in name_duplicates.values() if len(v) > 1]

        if md5_duplicates or name_duplicates_filtered:
            self.log("\n📁 **Duplicate Files Found:**")
            count = 1
            for group in md5_duplicates:
                for i in range(len(group) - 1):
                    self.log(f"{count}. \"{group[i]}\" and \"{group[i+1]}\"")
                    count += 1
            for group in name_duplicates_filtered:
                for i in range(len(group) - 1):
                    self.log(f"{count}. \"{group[i]}\" and \"{group[i+1]}\"")
                    count += 1

        elapsed = time.time() - start_time
        self.log(f"\n🕒 Execution Time: {int(elapsed // 3600):02d}:{int((elapsed % 3600) // 60):02d}:{int(elapsed % 60):02d}")
        self.log("\n✅ Finished processing all files.")

        self.write_log_file()
