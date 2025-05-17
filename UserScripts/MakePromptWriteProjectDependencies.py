import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../ScriptUtils")))
from Core.PromptContextCollector.PromptContextCollector import PromptContextCollector

PromptContextCollector(
    directories=[],
    files=[".gitmodules","Unity/TargetOne/Packages/manifest.json", "Unity/TargetOne/Assets/packages.config"],  # Wildcards and folders
    includes=[],
    ignores=[],
    template_path="UserScripts/MakePromptWriteProjectDependenciesTemplate.txt",  # Relative to project root
    template_vars={"additional_subdirectories": "DoTween"}, # todo: get directory listing here
    output_path="UserScripts/Outputs/PromptWriteProjectDependencies.txt"
).run()