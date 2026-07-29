import sys
from pathlib import Path


def get_root_dir(override_path: Path | str | None = None) -> Path:
    """
    Returns the root directory of the project or compiled executable.
    """
    if override_path is not None:
        return Path(override_path).resolve()
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).resolve().parent
    
    # User project execution mode: resolve to the current working directory
    return Path.cwd().resolve()