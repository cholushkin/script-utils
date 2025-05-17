import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils")))
from Core.Udio.AddNewTracks import AddNewTracks

AddNewTracks( 
    source_directory = r"SoundSources\udio\SoundSourcesTempBuffer", 
    track_target_path = r"SoundSources\udio\CompanyLogoTracks",
    move_files = True
    # log_level = "important"  - You can override global log level. Overriding chain: Config/default_config.jsong <- Config/user_config.jsong <- value from parameter log_level
).run()