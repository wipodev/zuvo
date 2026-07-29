import sys
from dataclasses import dataclass, field
from pathlib import Path

from zuvo.utils.paths import get_root_dir

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def _to_pkg_path(path_str: str) -> str:
    """Converts a filesystem style path 'src/app/commands' to a package 'src.app.commands'."""
    clean = path_str.replace("\\", "/").strip("/")
    return clean.replace("/", ".")


@dataclass
class Config:
    """Class representing the application configuration loaded from pyproject.toml."""

    # Project metadata
    name: str = "cli-app"
    version: str = "0.0.1"
    description: str = ""
    author: str = ""

    # Zuvo metadata
    app_type: str = "standard"
    title: str = "cli-app"
    executable_name: str = "cli-app"
    copyright: str = ""
    entry_point: str = "src/app/main.py"
    commands_pkg: str = "src.app.commands"
    locales_dir: Path = field(default_factory=lambda: Path("locales"))
    files: list[str] = field(default_factory=list)
    commands_config: dict[str, list[str]] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)
    modules: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, project_root: Path | str | None = None) -> "Config":
        """Loads configuration from a pyproject.toml file relative to the project root."""
        root = get_root_dir(project_root)
        toml_path = root / "pyproject.toml"

        if not toml_path.is_file() or tomllib is None:
            config = cls()
            config.locales_dir = root / "locales"
            return config

        try:
            with open(toml_path, "rb") as f:
                raw_data = tomllib.load(f)
        except Exception:
            config = cls()
            config.locales_dir = root / "locales"
            return config

        project = raw_data.get("project", {})
        zuvo = raw_data.get("tool", {}).get("zuvo", {})

        authors = project.get("authors", [])
        author_name = (
            authors[0].get("name", "")
            if authors and isinstance(authors[0], dict)
            else ""
        )
        name = project.get("name", "cli-app")
        raw_commands_dir = zuvo.get("commands_dir", "src/app/commands")
        raw_locales_dir = zuvo.get("locales_dir", "locales")

        return cls(
            name=name,
            version=project.get("version", "0.0.1"),
            description=project.get("description", ""),
            author=author_name,
            app_type=zuvo.get("type", "standard"),
            title=zuvo.get("title", name),
            executable_name=zuvo.get("executable_name", name),
            copyright=zuvo.get("copyright", ""),
            entry_point=zuvo.get("main", "src/app/main.py"),
            commands_pkg=_to_pkg_path(raw_commands_dir),
            locales_dir=root / raw_locales_dir,
            files=zuvo.get("files", []),
            commands_config=zuvo.get("commands", {}),
            scripts=zuvo.get("scripts", {}),
            modules=zuvo.get("modules", []),
        )


# ---------------------------------------------------------------------------
# Instancia activa e Interfaz de Constantes Globales
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = get_root_dir()

# Carga inicial por defecto
_current_config = Config.load(PROJECT_ROOT)

NAME: str = _current_config.name
VERSION: str = _current_config.version
DESCRIPTION: str = _current_config.description
AUTHOR: str = _current_config.author

APP_TYPE: str = _current_config.app_type
TITLE: str = _current_config.title
EXECUTABLE_NAME: str = _current_config.executable_name
COPYRIGHT: str = _current_config.copyright
ENTRY_POINT: str = _current_config.entry_point
COMMANDS_PKG: str = _current_config.commands_pkg
LOCALES_DIR: Path = _current_config.locales_dir
FILES: list[str] = _current_config.files
COMMANDS_CONFIG: dict[str, list[str]] = _current_config.commands_config
SCRIPTS: dict[str, str] = _current_config.scripts