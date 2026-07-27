import sys, os
from pathlib import Path


def get_root_dir() -> Path:
    """
    Returns the root directory of the project or compiled executable.
    """
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).resolve().parent
    
    # User project execution mode: resolve to the current working directory
    return Path(os.getcwd())


def get_locales_dir() -> Path:
    """Returns the path to the external language files directory."""
    return get_root_dir() / "locales"