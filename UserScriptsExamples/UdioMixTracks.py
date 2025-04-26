import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.Udio.MixTracks  import MixTracks 

MixTracks(
    look_folders=["UdioSources/tracks"],
    mix_override={
        "taraget_wildcard" : ["Ambient Echoes 15", "Hypnotic*"], # all tracks starting with 'Hypnotic' and 'Ambient Echoes 15'
        "json" : { # values presented here will override the original mix part of json
            "ignore": False, 
            "bitrate": "48k", # convert all of them to 48k
            "effects": {} # effects are overriden with empty dict, that means no effects will be applied (original dry mix)
        }        
    }
).run()