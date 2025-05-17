import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils")))
from Core.Udio.MixTracks  import MixTracks 

target_bitrate="96k"

MixTracks(
    look_folders=["SoundSources/udio/CompanyLogoTracks"],
    mix_override={
        # "taraget_wildcard" : ["Ambient Echoes 15", "Hypnotic*"], # all tracks starting with 'Hypnotic' and 'Ambient Echoes 15'
        "json" : { # values presented here will override the original mix part of json
            "ignore": False, 
            "bitrate": target_bitrate # convert all of them to target bitrate
            # "effects": {} # if effects are overriden with empty dict, that means no effects will be applied (original dry mix)
        }        
    }
).run()