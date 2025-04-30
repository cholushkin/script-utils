import os
import subprocess
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from Core.LogManager import LogManager
from Core.ConfigManager import ConfigManager

class GitSubmoduleManager:
    def __init__(self, log_level=None):
        self.project_root = self.find_git_root()
        self.config = ConfigManager().load_config()
        default_level = self.config.get("log_level", "normal")
        self.log_manager = LogManager(log_level or default_level)

    def find_git_root(self):
        current_dir = os.getcwd()
        while not os.path.exists(os.path.join(current_dir, ".git")):
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                raise Exception("Not inside a Git repository.")
            current_dir = parent_dir
        return current_dir

    def add_git_submodule(self, repo_url, submodule_path):
        try:
            os.chdir(self.project_root)  # ensure we're at root
            submodule_path = os.path.normpath(submodule_path)  # normalize any slashes
            subprocess.run(["git", "submodule", "add", repo_url, submodule_path], check=True)
            self.log_manager.log("normal", f"✅ Submodule added: {submodule_path}")
            self.update_submodule(submodule_path)
        except subprocess.CalledProcessError as e:
            self.log_manager.log("important", f"❌ Failed to add submodule: {e}")
        except Exception as e:
            self.log_manager.log("important", f"❌ Error: {e}")

    def remove_git_submodule(self, submodule_path):
        try:
            os.chdir(self.project_root)
            subprocess.run(["git", "submodule", "deinit", "-f", submodule_path], check=True)
            subprocess.run(["git", "rm", "-f", submodule_path], check=True)
            subprocess.run(["rm", "-rf", f".git/modules/{submodule_path}"], shell=True)
            if os.path.exists(submodule_path):
                os.system(f"rm -rf {submodule_path}")
            self.log_manager.log("normal", f"🧹 Submodule removed: {submodule_path}")
        except subprocess.CalledProcessError as e:
            self.log_manager.log("important", f"❌ Git command failed: {e}")
        except Exception as e:
            self.log_manager.log("important", f"❌ Error: {e}")

    def update_submodule(self, submodule_path):
        try:
            subprocess.run(["git", "submodule", "update", "--init", submodule_path], check=True)
            self.log_manager.log("normal", f"🔄 Submodule updated: {submodule_path}")
        except subprocess.CalledProcessError as e:
            self.log_manager.log("important", f"❌ Failed to update submodule: {e}")
