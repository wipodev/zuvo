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
    Converts a filesystem path or dot-notation string to a Python package import path.
    Strips leading 'src/' or 'src.' to support standard src-layout packaging.

    Args:
        path_str (str): File system path or dot notation string.

    Returns:
        str: Clean package dot-notation path (e.g., 'app.commands').
    """
    clean = path_str.replace("\\", "/").strip("/")    
    if clean.startswith("src/"):
        clean = clean[4:]
        
    pkg = clean.replace("/", ".")
    
    if pkg.startswith("src."):
        pkg = pkg[4:]

    return pkg


def resolve_entry_point(script_target: str, root: Path) -> str:
    """
    Resolves a script target (e.g., 'app.main:main') to a valid relative filesystem path.
    Checks if the source file resides within 'src/' or directly in root.

    Args:
        script_target (str): Entry point specifier from project.scripts (e.g. 'app.main:main').
        root (Path): Absolute path to the project root directory.

    Returns:
        str: Relative filesystem path to the entry point script (e.g. 'src/app/main.py').
    """
    module_part = script_target.split(":")[0]
    relative_path = module_part.replace(".", "/") + ".py"

    if (root / "src" / relative_path).is_file():
        return f"src/{relative_path}"

    return relative_path