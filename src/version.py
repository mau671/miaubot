#!/usr/bin/env python3
"""Version management utilities for MiauBot."""

import os
from pathlib import Path

def get_version():
    """Get the current version from VERSION file."""
    version_file = Path(__file__).parent.parent / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "unknown"

def get_version_info():
    """Get detailed version information."""
    version = get_version()
    try:
        import subprocess
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], 
            stderr=subprocess.DEVNULL
        ).decode().strip()
        git_dirty = subprocess.call(
            ["git", "diff", "--quiet"], 
            stderr=subprocess.DEVNULL, 
            stdout=subprocess.DEVNULL
        ) != 0
        git_info = f"{git_hash}{'-dirty' if git_dirty else ''}"
    except Exception:
        git_info = "unknown"
    
    return {
        "version": version,
        "git": git_info,
        "full": f"{version}+{git_info}" if git_info != "unknown" else version
    }

__version__ = get_version()

if __name__ == "__main__":
    info = get_version_info()
    print(f"Version: {info['version']}")
    print(f"Git: {info['git']}")
    print(f"Full: {info['full']}") 