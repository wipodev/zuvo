import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zuvo.utils.paths import get_root_dir, resolve_entry_point, to_pkg_path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


@dataclass
class Config:
    """Class representing the application configuration loaded from pyproject.toml."""

    # Project metadata
    name: str = "cli-app"
    version: str = "0.0.1"
    description: str = ""
    author: str = ""

    # Zuvo runtime metadata
    title: str = "cli-app"
    copyright: str = "Copyright (c) 2026"
    cli_name: str = "cli-app"
    commands_pkg: str = "app.commands"
    commands_config: dict[str, list[str]] = field(default_factory=dict)
    scripts: dict[str, str] = field(default_factory=dict)

    # Build settings ([tool.zuvo.build])
    build: dict[str, Any] = field(
        default_factory=lambda: {
            "compiler": "pyinstaller",
            "entry_point": "src/app/main.py",
            "company_name": "",
            "icon": "",
            "files": [],
            "output_dir": "dist",
        }
    )

    # Inno Setup settings ([tool.zuvo.inno])
    inno: dict[str, Any] = field(
        default_factory=lambda: {
            "inno_path": "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
            "app_publisher_url": "",
            "license_file": "",
            "default_dir_name": "{autopf}\\cli-app",
            "output_base_filename": "installer",
        }
    )

    def to_dict(self) -> dict[str, Any]:
        """Converts config instance into a dictionary suitable for codegen."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "title": self.title,
            "copyright": self.copyright,
            "cli_name": self.cli_name,
            "commands_pkg": self.commands_pkg,
            "commands_config": self.commands_config,
            "scripts": self.scripts,
            "build": self.build,
            "inno": self.inno,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        """Reconstructs a Config instance from a dictionary."""
        return cls(**data.copy())

    @classmethod
    def load(cls, project_root: Path | str | None = None) -> "Config":
        """Loads configuration from a pyproject.toml file relative to the project root."""
        root = get_root_dir(project_root)
        toml_path = root / "pyproject.toml"

        if not toml_path.is_file() or tomllib is None:
            return cls()

        try:
            with open(toml_path, "rb") as f:
                raw_data = tomllib.load(f)
        except Exception:
            return cls()

        project = raw_data.get("project", {})
        zuvo = raw_data.get("tool", {}).get("zuvo", {})
        zuvo_build = zuvo.get("build", {})
        zuvo_inno = zuvo.get("inno", {})

        # Extract project name and author
        name = project.get("name", "cli-app")
        authors = project.get("authors", [])
        author_name = (
            authors[0].get("name", "")
            if authors and isinstance(authors[0], dict)
            else ""
        )

        # Extract CLI name and resolve entry_point for build
        scripts_dict = project.get("scripts", {})
        if scripts_dict:
            cli_name = next(iter(scripts_dict))
            script_target = scripts_dict[cli_name]
            entry_point = resolve_entry_point(script_target, root)
        else:
            cli_name = name
            entry_point = "src/app/main.py"

        # Build configurations with defaults fallback
        default_config = cls()
        merged_build = {
            **default_config.build,
            "entry_point": entry_point,
            **zuvo_build,
        }
        
        default_inno = {
            **default_config.inno,
            "default_dir_name": f"{{autopf}}\\{cli_name}",
        }
        merged_inno = {**default_inno, **zuvo_inno}

        raw_commands_pkg = zuvo.get("commands_pkg", "app.commands")

        return cls(
            name=name,
            version=project.get("version", "0.0.1"),
            description=project.get("description", ""),
            author=author_name,
            title=zuvo.get("title", name),
            copyright=zuvo.get("copyright", "Copyright (c) 2026"),
            cli_name=cli_name,
            commands_pkg=to_pkg_path(raw_commands_pkg),
            commands_config=zuvo.get("commands", {}),
            scripts=zuvo.get("scripts", {}),
            build=merged_build,
            inno=merged_inno,
        )


# ---------------------------------------------------------------------------
# CENTRAL REGISTRY (Passive Warehouse)
# ---------------------------------------------------------------------------
_instance: Config | None = None


def set_config(config: Config) -> None:
    """Stores the active explicit configuration loaded at runtime."""
    global _instance
    _instance = config


def get_config() -> Config:
    """Retrieves the active configuration instance across modules."""
    if _instance is None:
        raise RuntimeError("Configuration has not been initialized with set_config().")
    return _instance