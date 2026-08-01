import sys, importlib.util
from pathlib import Path
from importlib.resources import files


def get_locales_dir(package_name: str = "app") -> Path:
    """Resolves the directory containing application translation files.

    Checks for frozen executable environments, local development layouts
    (including src-layout), or falls back to inspecting installed Python package resources.

    Args:
        package_name (str): Root package name used to locate installed resources.

    Returns:
        Path: Resolved path pointing to the active locales directory.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "locales"

    # 1. Local development layout check (src/package_name/locales)
    src_locales = Path.cwd() / "src" / package_name / "locales"
    if src_locales.is_dir():
        return src_locales

    # 2. Flat development layout check (package_name/locales)
    flat_locales = Path.cwd() / package_name / "locales"
    if flat_locales.is_dir():
        return flat_locales

    # 3. Installed package lookup (via importlib.resources)
    try:
        pkg_locales = Path(str(files(package_name).joinpath("locales")))
        if pkg_locales.is_dir():
            return pkg_locales
    except Exception:
        pass

    return flat_locales


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


def resolve_entry_point(script_target: str) -> str:
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

    return f"src/{relative_path}"


def resolve_entry_commands(entry_package: str) -> Path:
    """
    Converts a Python module dot-notation path or raw relative path into a Path object.

    Args:
        entry_package: The package path declared in configuration (e.g., "my_cli.commands").

    Returns:
        Path: Relative Path object targeting the commands directory.
    """
    clean_commands = entry_package.replace(".", "/")
    flat_commands = Path(clean_commands)
    src_commands = Path("src" / flat_commands)

    if Path(Path.cwd() / src_commands).is_dir():
        return src_commands

    if Path(Path.cwd() / flat_commands).is_dir():
        return flat_commands

    return Path(clean_commands)


def resolve_command_module(base_pkg: str, app_name: str, cmd_name: str) -> tuple[str, bool]:
    """
    Resolves the Python import package path for a given command.
    Checks modular structure (base_pkg.app_name.cmd_name) first,
    then falls back to flat structure (base_pkg.cmd_name).

    Args:
        base_pkg: The root commands package (e.g., 'zuvo.commands').
        app_name: The application context name (e.g., 'app1').
        cmd_name: The target command stem (e.g., 'build').

    Returns:
        tuple[str, bool]: (resolved_import_path, exists_on_disk)
    """
    modular_import = f"{base_pkg}.{app_name}.{cmd_name}"
    flat_import = f"{base_pkg}.{cmd_name}"

    # 1. Check modular path (commands/app_name/cmd_name.py)
    try:
        if importlib.util.find_spec(modular_import) is not None:
            return modular_import, True
    except (ModuleNotFoundError, ValueError, AttributeError):
        pass

    # 2. Check flat path fallback (commands/cmd_name.py)
    try:
        if importlib.util.find_spec(flat_import) is not None:
            return flat_import, True
    except (ModuleNotFoundError, ValueError, AttributeError):
        pass

    return modular_import, False


def scan_command_files(commands_dir: Path) -> dict[str, list[str]]:
    """
    Recursively scans the given commands directory and categorizes Python command files
    by their parent subfolder. Root files are assigned to the 'root' key.

    Args:
        commands_dir (Path): Absolute or relative Path to the commands directory.

    Returns:
        dict[str, list[str]]: Mapping of subfolder names (or 'root') to sorted list of command stems.
    """
    categorized_commands: dict[str, list[str]] = {}

    if not commands_dir.exists() or not commands_dir.is_dir():
        return categorized_commands

    for file in commands_dir.rglob("*.py"):
        if file.name.startswith("_"):
            continue

        relative_path = file.relative_to(commands_dir)
        parent_parts = relative_path.parent.parts

        # Determine category key: 'root' if direct child, otherwise top-most subfolder
        category_key = parent_parts[0] if parent_parts else "root"

        if category_key not in categorized_commands:
            categorized_commands[category_key] = []

        categorized_commands[category_key].append(file.stem)

    for key in categorized_commands:
        categorized_commands[key].sort()

    return categorized_commands