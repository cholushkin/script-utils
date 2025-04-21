import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Core")))
from ConfigManager import ConfigManager

ConfigManager().print()