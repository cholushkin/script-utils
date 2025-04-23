// --- Source Blob ---

// --- Start File: ScriptUtils\Core\PromptContextCollector\PromptContextCollector.py ---

import os
import fnmatch
import re

class PromptContextCollector:
    def __init__(self, directories, includes, ignores, template_path, template_vars, output_path):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",".."))
        self.directories = directories
        self.includes = includes
        self.ignores = ignores
        self.template_path = os.path.join(self.project_root, template_path)
        self.output_path = os.path.join(self.project_root, output_path)  # ← Fix here
        self.template_vars = template_vars
        self.collected_files = []


    def _match_patterns(self, path, patterns):
        return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

    def _should_include(self, file_path):
        filename = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, self.project_root)
        return self._match_patterns(filename, self.includes) and not self._match_patterns(rel_path, self.ignores)

    def _resolve_paths(self):
        resolved = set()
        for pattern in self.directories:
            abs_pattern = os.path.join(self.project_root, pattern)
            if os.path.isdir(abs_pattern):
                resolved.add(abs_pattern)
            else:
                dir_part = os.path.dirname(abs_pattern) or "."
                for root, _, files in os.walk(dir_part):
                    for file in files:
                        full_path = os.path.join(root, file)
                        if fnmatch.fnmatch(full_path, abs_pattern):
                            resolved.add(os.path.dirname(full_path))
        return list(resolved)

    def _substitute_template(self):
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template file not found: {self.template_path}")
        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()
        for key, value in self.template_vars.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template

    def run(self):
        print(f"🛠 Starting PromptContextCollector")
        print(f"📁 Project Root: {self.project_root}")
        print(f"📂 Directories: {self.directories}")
        print(f"📄 Includes: {self.includes}")
        print(f"🚫 Ignores: {self.ignores}")
        print(f"📜 Template Path: {self.template_path}")
        print(f"📤 Output Path: {self.output_path}")
        print("-" * 50)

        collected = 0
        with open(self.output_path, 'w', encoding='utf-8') as out:
            out.write("// --- Source Blob ---\n\n")

            for base_dir in self._resolve_paths():
                for root, _, files in os.walk(base_dir):
                    if self._match_patterns(os.path.relpath(root, self.project_root), self.ignores):
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        if not self._should_include(file_path):
                            continue
                        rel_path = os.path.relpath(file_path, self.project_root)
                        try:
                            with open(file_path, "r", encoding="utf-8") as src:
                                out.write(f"// --- Start File: {rel_path} ---\n\n")
                                out.write(src.read())
                                out.write(f"\n\n// --- End File: {rel_path} ---\n\n")
                            self.collected_files.append(rel_path)
                            print(f"✅ Added: {rel_path}")
                            collected += 1
                        except Exception as e:
                            print(f"❌ Error reading {rel_path}: {e}")
                            out.write(f"// !!! Error reading file {rel_path}: {e} !!!\n\n")

            prompt_text = self._substitute_template()
            out.write("\n" + "-" * 50 + "\n")
            out.write("// --- Prompt ---\n\n")
            out.write(prompt_text)

        print("-" * 50)
        print(f"🎯 Collection complete: {collected} file(s) added.")
        print(f"📝 Output written to: {self.output_path}")


// --- End File: ScriptUtils\Core\PromptContextCollector\PromptContextCollector.py ---


--------------------------------------------------
// --- Prompt ---

- You are reviewing Python scripts for a tool designed to collect source files and generate an AI-ready prompt.
- Your task is to create a well-structured and user-friendly `README.md` that includes the following sections:

## Introduction
- Provide a brief overview of the tool from the user's perspective.
- Explain its purpose and the problem it solves.

## Features
- List the key capabilities of the tool as bullet points.

## Summary
- Conclude with a concise summary highlighting the tool’s value and primary use case.

Also:
- Provide two versions of your response: one concise and one more detailed.
