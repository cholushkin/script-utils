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

    # -------------------------
    # Core helpers
    # -------------------------

    def run_git(self, args, cwd=None):
        """Run git command safely"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.log_manager.log("important", f"❌ Git error: {' '.join(args)}")
            self.log_manager.log("important", e.stderr.strip())
            raise

    def find_git_root(self):
        current_dir = os.getcwd()
        while not os.path.exists(os.path.join(current_dir, ".git")):
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                raise Exception("Not inside a Git repository.")
            current_dir = parent_dir
        return current_dir

    # -------------------------
    # Submodule basics
    # -------------------------

    def add_git_submodule(self, repo_url, submodule_path):
        try:
            os.chdir(self.project_root)
            submodule_path = os.path.normpath(submodule_path)

            self.run_git(["submodule", "add", repo_url, submodule_path])
            self.log_manager.log("normal", f"✅ Submodule added: {submodule_path}")

            self.update_submodule(submodule_path)

        except Exception as e:
            self.log_manager.log("important", f"❌ Error: {e}")

    def remove_git_submodule(self, submodule_path):
        try:
            os.chdir(self.project_root)

            self.run_git(["submodule", "deinit", "-f", submodule_path])
            self.run_git(["rm", "-f", submodule_path])

            modules_path = os.path.join(self.project_root, ".git", "modules", submodule_path)
            if os.path.exists(modules_path):
                subprocess.run(["rm", "-rf", modules_path], shell=True)

            if os.path.exists(submodule_path):
                subprocess.run(["rm", "-rf", submodule_path], shell=True)

            self.log_manager.log("normal", f"🧹 Submodule removed: {submodule_path}")

        except Exception as e:
            self.log_manager.log("important", f"❌ Error: {e}")

    def update_submodule(self, submodule_path):
        try:
            self.run_git(["submodule", "update", "--init", submodule_path])
            self.log_manager.log("normal", f"🔄 Submodule updated: {submodule_path}")
        except Exception as e:
            self.log_manager.log("important", f"❌ Failed to update submodule: {e}")

    # -------------------------
    # Advanced functionality
    # -------------------------

    def get_submodules(self):
        """Return list of submodule paths"""
        output = self.run_git(["config", "--file", ".gitmodules", "--get-regexp", "path"])
        submodules = []

        for line in output.splitlines():
            parts = line.strip().split(" ")
            if len(parts) == 2:
                submodules.append(parts[1])

        return submodules

    def get_default_branch(self, submodule_path):
        """Detect default branch (main/master/etc)"""
        try:
            ref = self.run_git(
                ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                cwd=submodule_path
            )
            return ref.replace("origin/", "")
        except Exception:
            return "master"  # fallback

    def checkout_branch(self, submodule_path, branch):
        """Ensure submodule is on a branch (fix detached HEAD)"""
        try:
            self.run_git(["checkout", branch], cwd=submodule_path)
        except Exception:
            # create branch if not exists
            self.run_git(["checkout", "-b", branch, f"origin/{branch}"], cwd=submodule_path)

    def update_submodule_to_latest(self, submodule_path):
        """Update a single submodule to latest commit"""
        try:
            self.log_manager.log("normal", f"🔄 Updating: {submodule_path}")

            # fetch
            self.run_git(["fetch", "origin"], cwd=submodule_path)

            # detect branch
            branch = self.get_default_branch(submodule_path)
            self.log_manager.log("normal", f"  → branch: {branch}")

            # fix detached HEAD
            self.checkout_branch(submodule_path, branch)

            # pull latest
            self.run_git(["pull", "origin", branch], cwd=submodule_path)

        except Exception as e:
            self.log_manager.log("important", f"❌ Failed updating {submodule_path}: {e}")

    def force_update_all_submodules(self):
        """
        🔥 MAIN FEATURE:
        - Updates ALL submodules to latest remote
        - Fixes detached HEAD
        - Stages changes in root repo
        """
        try:
            os.chdir(self.project_root)

            self.log_manager.log("normal", "===> Syncing submodules")
            self.run_git(["submodule", "sync", "--recursive"])

            self.log_manager.log("normal", "===> Initializing submodules")
            self.run_git(["submodule", "update", "--init", "--recursive"])

            submodules = self.get_submodules()

            if not submodules:
                self.log_manager.log("normal", "No submodules found.")
                return

            for sub in submodules:
                full_path = os.path.join(self.project_root, sub)
                self.update_submodule_to_latest(full_path)

            # 🔥 THIS IS CRITICAL STEP
            self.log_manager.log("normal", "===> Staging updated submodule pointers")
            self.run_git(["add", "."])

            self.log_manager.log("normal", "✅ All submodules updated and staged.")

        except Exception as e:
            self.log_manager.log("important", f"❌ Force update failed: {e}")