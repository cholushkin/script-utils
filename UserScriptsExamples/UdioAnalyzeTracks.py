import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.Udio.AnalyzeTrackDB  import AnalyzeTrackDB 

AnalyzeTrackDB(
    look_folders=["d:/projects/dev/target-one/SoundSources/udio/tracks"],
    output_txt="ScriptUtils/UserScriptsExamples/UdioAnalyzeTrackOutput/tracks_log.txt",
    estimate_bitrates=["48k", "128k", "192k"],
).run()