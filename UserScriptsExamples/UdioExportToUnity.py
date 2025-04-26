import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.Udio.ExportTracks import ExportTracks

ExportTracks(
    look_folders = ["UdioSources/tracks"], 
    unity_dest_path = "Assets/Music", 
).run()