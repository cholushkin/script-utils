import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.Udio.MixTracks  import MixTracks 

MixTracks(
    look_folders=["UdioSources/tracks"]
).run()