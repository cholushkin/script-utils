import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils")))
from Core.Udio.ExportTracks import ExportTracks

ExportTracks(
    look_folders = ["SoundSources/udio/tracks"], 
    unity_dest_path = "Assets/Core/Music/StreamingAssets/GameTracks",
    music_configuration = "GameTracks.asset"
).run()

ExportTracks(
    look_folders = ["SoundSources/udio/CompanyLogoTracks"], 
    unity_dest_path = "Assets/Core/Music/StreamingAssets/IntroTracks", 
    music_configuration = "IntroTracks.asset"
).run()