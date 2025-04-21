import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Core.BackupUtil.BackupUtil import BackupUtil

folders_to_backup = ["UdioSources", "Unity"]
exclude_patterns = ["*.tmp", "*.log", "__pycache__"]
destination_path = "d:/backups/udio-backup-{DATE}.zip"

# Run backup
BackupUtil(destination_path, folders_to_backup, exclude_patterns).run()