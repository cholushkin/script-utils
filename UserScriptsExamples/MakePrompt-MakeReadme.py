import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.PromptContextCollector.PromptContextCollector import PromptContextCollector

PromptContextCollector(
    directories=["ScriptUtils/Core/PromptContextCollector/**"],  # Wildcards and folders
    includes=["*.py"],
    ignores=["*/Tests/*", "*.meta", "__pycache__"],
    template_path="ScriptUtils/UserScriptsExamples/CreateReadmePromptTemplate.txt",  # Relative to project root
    template_vars={"additional_task_0": "Provide two versions of your response: one concise and one more detailed."},
    output_path="ScriptUtils/UserScriptsExamples/OutputPrompts/PromptMakeReadmeForPromptCollector.txt"
).run()