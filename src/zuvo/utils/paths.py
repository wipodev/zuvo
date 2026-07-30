import sys
from pathlib import Path


def get_root_dir(override_path: Path | str | None = None) -> Path:
    """
    Resolves the active project or binary root directory.

    Handles explicit path overrides, frozen executable environments 
    (such as PyInstaller/Nuitka extraction dirs or binary locations), 
    and falls back to the current working directory for local execution.

    Args:
        override_path (Path | str | None): Optional custom path to force 
            as the root directory.

    Returns:
        Path: Absolute resolved path to the root directory.
    """
    if override_path is not None:
        return Path(override_path).resolve()
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).resolve().parent
    
    return Path.cwd().resolve()

def to_pkg_path(path_str: str) -> str:
    """
    Converts a filesystem style path ('src/app/commands') to a Python package path ('src.app.commands').

    Args:
        path_str (str): File system path string.

    Returns:
        str: Dot-separated package path.
    """
    clean = path_str.replace("\\", "/").strip("/")
    return clean.replace("/", ".")