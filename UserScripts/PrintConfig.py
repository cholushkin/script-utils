import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils", "Core")))
from ConfigManager import ConfigManager

ConfigManager().print()