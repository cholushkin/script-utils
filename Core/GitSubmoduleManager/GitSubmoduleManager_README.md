# GitSubmoduleManager (Core Module)

## Overview

**GitSubmoduleManager** is a core utility module that simplifies the
management of Git submodules within a project.

It provides a clean Python interface for:

-   Adding submodules
-   Removing submodules
-   Updating submodules
-   Ensuring execution from repository root
-   Logging Git operations consistently

This module is intended to automate dependency management across
projects.

------------------------------------------------------------------------

## Location

    ScriptUtils/Core/GitSubmoduleManager/GitSubmoduleManager.py

------------------------------------------------------------------------

## Features

-   Automatic Git repository root detection
-   Safe execution of Git commands via `subprocess`
-   Add + initialize submodules
-   Remove submodules cleanly (including .git/modules cleanup)
-   Update / reinitialize submodules
-   Integrated logging using `LogManager`
-   Uses global configuration via `ConfigManager`

------------------------------------------------------------------------

## Initialization

``` python
GitSubmoduleManager(log_level=None)
```

### Parameters

  Parameter     Type   Description
  ------------- ------ -------------------------------------
  `log_level`   str    Optional override for logging level

If not provided, log level is read from project configuration.

------------------------------------------------------------------------

## Example Usage

``` python
from Core.GitSubmoduleManager.GitSubmoduleManager import GitSubmoduleManager

manager = GitSubmoduleManager()

# Add a submodule
manager.add_git_submodule(
    repo_url="https://github.com/example/library.git",
    submodule_path="External/Library"
)

# Update submodule
manager.update_submodule("External/Library")

# Remove submodule
manager.remove_git_submodule("External/Library")
```

------------------------------------------------------------------------

## Methods

### add_git_submodule(repo_url, submodule_path)

-   Executes `git submodule add`
-   Automatically initializes the submodule
-   Logs success or failure

------------------------------------------------------------------------

### remove_git_submodule(submodule_path)

-   Runs:
    -   `git submodule deinit -f`
    -   `git rm -f`
    -   Removes `.git/modules/<path>`
-   Cleans working directory
-   Logs result

------------------------------------------------------------------------

### update_submodule(submodule_path)

-   Runs `git submodule update --init`
-   Reinitializes submodule if needed

------------------------------------------------------------------------

## How It Works

1.  Detects Git root by traversing parent directories.
2.  Ensures all operations are executed from repository root.
3.  Executes Git commands using `subprocess.run()`.
4.  Logs output using centralized logging system.

------------------------------------------------------------------------

## Configuration

Uses:

    ScriptUtils/Config/default_config.json
    ScriptUtils/Config/user_config.json

Respects:

-   `log_level`

------------------------------------------------------------------------

## Requirements

-   Git must be installed and accessible from system PATH.
-   Must be executed inside a valid Git repository.
-   User must have necessary permissions for submodule operations.

------------------------------------------------------------------------

## Use Cases

-   Centralized dependency management
-   Automated project setup scripts
-   CI/CD repository bootstrapping
-   Multi-repository architecture management

------------------------------------------------------------------------

## Notes

-   If not inside a Git repository, initialization will raise an
    exception.
-   Removal includes cleanup of `.git/modules` to avoid orphaned
    metadata.
-   Designed for scripted automation --- not interactive Git usage.

------------------------------------------------------------------------

Generated on: 2026-02-18 22:32:22
