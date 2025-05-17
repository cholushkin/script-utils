import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils")))
from Core.PromptContextCollector.PromptContextCollector import PromptContextCollector

PromptContextCollector(
    files=[],
    directories=["Unity/TargetOne/Assets/Core/Runtime/Music"],  # Wildcards and folders
    includes=["*.cs"],
    ignores=[],
    template_path="UserScripts/MakePromptWriteReadmeTemplate.txt",  # Relative to project root
    template_vars={"module_name": "Music"},
    output_path="UserScripts/Outputs/PromptWriteReadme.txt"
).run()