import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.Udio.AnalyzeTrackDB  import AnalyzeTrackDB 

AnalyzeTrackDB(
    look_folders=["UdioSources/tracks"],
    output_json="ScriptUtils/UserScriptsExamples/UdioAnalyzeTrackOutput/tracks_meta.json",
    output_txt="ScriptUtils/UserScriptsExamples/UdioAnalyzeTrackOutput/tracks_log.txt",
    estimate_bitrates=["48k", "128k"],
    detect_abrupt_end=False
).run()
