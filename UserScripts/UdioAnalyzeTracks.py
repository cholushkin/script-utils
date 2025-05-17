import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils")))
from Core.Udio.AnalyzeTrackDB  import AnalyzeTrackDB 

AnalyzeTrackDB(
    look_folders=[r"SoundSources\udio\tracks"],
    estimate_bitrates=["48k", "128k", "192k"],
).run()