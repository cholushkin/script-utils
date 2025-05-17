import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils")))
from Core.PromptContextCollector.PromptContextCollector import PromptContextCollector

PromptContextCollector(
    directories=["Unity/TargetOne/Assets/Core/Runtime/Music/**"],  # Wildcards and folders
    includes=["*.cs"],
    ignores=[],
    template_path="UserScripts/MakePromptAnalyzeScriptTemplate.txt",  # Relative to project root
    template_vars={"additional_task_0": "Share ideas to expand the concept and introduce innovative or interesting new features."},
    output_path="UserScripts/Outputs/PromptAnalyzeMusicModule.txt"
).run()