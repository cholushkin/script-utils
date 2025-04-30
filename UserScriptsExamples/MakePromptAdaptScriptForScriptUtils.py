import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.PromptContextCollector.PromptContextCollector import PromptContextCollector

PromptContextCollector(
    directories=[
        "ScriptUtils/Core/**",
        "ScriptUtils/Config/*.json",
        "ScriptUtils/UserScriptsExamples/*.py"
    ],  # Wildcards and folders
    includes=["*.py","*.json"],
    ignores=["*/Tests/*", "*.meta", "__pycache__", "ScriptUtils/Core/Udio/Effects", "ScriptUtils/Core/Udio/AddNewTracksJsonTemplate.json"],
    template_path="ScriptUtils/UserScriptsExamples/MakePromptAdaptScriptForScriptUtilsTemplate.txt",  # Relative to project root
    template_vars={"target_script": "git_submodule_manager"},
    output_path="ScriptUtils/UserScriptsExamples/MakePromptOutput/PromptAdaptScriptForScriptUtils.txt"
).run()