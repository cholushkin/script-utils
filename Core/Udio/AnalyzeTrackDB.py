import os
import json
import hashlib
import time
from mutagen.mp3 import MP3

class AnalyzeTrackDB:
    def __init__(self, look_folders, output_txt, estimate_bitrates):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # project root
        self.output_txt = os.path.join(self.project_root, output_txt)
        self.look_folders = [os.path.join(self.project_root, folder) for folder in look_folders]
        self.estimate_bitrates = estimate_bitrates
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

    def read_track_metadata_from_json(self, json_file):
        metadata = {"energy": None, "mood": None, "pop": None, "stars": None}
        if os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "tags" in data:
                        metadata.update({
                            "energy": data["tags"].get("energy"),
                            "mood": data["tags"].get("mood"),
                            "pop": data["tags"].get("pop"),
                            "stars": data["tags"].get("stars")
                        })
            except Exception as e:
                self.log(f"⚠️ Error reading {json_file}: {e}")
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
        md5_hashes = {}
        name_duplicates = {}

        self.log("🔍 Searching for MP3 files with corresponding JSON metadata...\n")

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
                    json_file = os.path.splitext(file_path)[0] + ".json"
                    file_name = os.path.splitext(file)[0]
                    has_json = os.path.exists(json_file)
                    json_emoji = " 📄" if has_json else " 📄❌"

                    if not has_json:
                        self.log(f"⚠️ Warning: JSON metadata not found for {file}")
                        continue

                    metadata = self.read_track_metadata_from_json(json_file)
                    energy = metadata["energy"]
                    mood = metadata["mood"]
                    pop = metadata["pop"]
                    stars = metadata["stars"]

                    duration_seconds, duration_str = self.get_mp3_duration(file_path)

                    md5 = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
                    md5_hashes.setdefault(md5, []).append(file_path)
                    name_duplicates.setdefault(file, []).append(file_path)

                    # Format and log metadata
                    line = f"- {file} [{duration_str}]{json_emoji}"
                    if energy is not None: line += f" 🔥{energy:.1f}"
                    if mood is not None:   line += f" 😊{mood:.1f}"
                    if pop is not None:    line += f" 🎵{pop:.1f}"
                    if stars is not None:  line += f" ✨{int(stars)}"

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

        self.log("\n=== Summary ===")
        self.log(f"🎼 Total MP3 files analyzed (with JSON metadata): {mp3_count}")
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
                    self.log(f"{count}. \"{group[i]}\" and \"{group[i+1]}\" (Same MD5)")
                    count += 1
            for group in name_duplicates_filtered:
                for i in range(len(group) - 1):
                    self.log(f"{count}. \"{group[i]}\" and \"{group[i+1]}\" (Same Name)")
                    count += 1

        elapsed = time.time() - start_time
        self.log(f"\n🕒 Execution Time: {int(elapsed // 3600):02d}:{int((elapsed % 3600) // 60):02d}:{int(elapsed % 60):02d}")
        self.log("\n✅ Finished analyzing files.")
        print(f"Log saved to {self.output_txt}")

        self.write_log_file()

 