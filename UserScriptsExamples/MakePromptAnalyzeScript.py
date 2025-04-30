import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.PromptContextCollector.PromptContextCollector import PromptContextCollector

PromptContextCollector(
    directories=["ScriptUtils/Core/PromptContextCollector/**"],  # Wildcards and folders
    includes=["*.py"],
    ignores=["*/Tests/*", "*.meta", "__pycache__"],
    template_path="ScriptUtils/UserScriptsExamples/MakePromptAnalyzeScriptTemplate.txt",  # Relative to project root
    template_vars={"additional_task_0": "Share ideas to expand the concept and introduce innovative or interesting new features."},
    output_path="ScriptUtils/UserScriptsExamples/MakePromptOutput/PromptContextCollectorScriptAnalysis.txt"
).run()