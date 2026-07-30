import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        """Converts config instance into a dictionary suitable for codegen."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "app_type": self.app_type,
            "title": self.title,
            "executable_name": self.executable_name,
            "copyright": self.copyright,
            "entry_point": self.entry_point,
            "commands_pkg": self.commands_pkg,
            "locales_dir": str(self.locales_dir),
            "files": self.files,
            "commands_config": self.commands_config,
            "scripts": self.scripts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Reconstructs a Config instance from a dictionary."""
        data_copy = data.copy()
        if "locales_dir" in data_copy:
            data_copy["locales_dir"] = Path(data_copy["locales_dir"])
        return cls(**data_copy)

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
        )

# ---------------------------------------------------------------------------
# CENTRAL REGISTRY (Passive Warehouse)
# ---------------------------------------------------------------------------
_instance: Config | None = None

def set_config(config: Config) -> None:
    """Guarda la instancia explícita cargada en el punto de entrada."""
    global _instance
    _instance = config

def get_config() -> Config:
    """Obtiene la instancia activa desde cualquier módulo."""
    if _instance is None:
        raise RuntimeError("La configuración no ha sido inicializada con set_config().")
    return _instance