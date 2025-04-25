import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.Udio.AddNewTracks import AddNewTracks

AddNewTracks( 
    source_directory = r"UdioSources\UdioDownload", 
    track_target_path = r"UdioSources\tracks",
    move_files = False
).run()