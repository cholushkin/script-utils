import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils")))
from Core.Udio.MixTracks  import MixTracks 

MixTracks(
    look_folders=["SoundSources/udio/tracks"]    
).run()

MixTracks(
    look_folders=["SoundSources/udio/CompanyLogoTracks"]    
).run()