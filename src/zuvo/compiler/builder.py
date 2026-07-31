from dataclasses import dataclass, field
from pathlib import Path
import sys

from zuvo.core.config import Config
from zuvo.utils.paths import get_locales_dir, get_root_dir


@dataclass
class BuildOptions:
    """Normalized build configuration resolved from Config and system context."""

    entry_point: Path
    dist_dir: Path
    exe_name: str
    version_str: str
    commands_pkg: str
    locales_dir: Path | None
    company_name: str
    title: str
    description: str
    copyright: str
    icon_path: Path | None
    extra_files: list[str] = field(default_factory=list)

    @classmethod
    def from_config(
        cls, cfg: Config, project_root: Path | str | None = None
    ) -> "BuildOptions":
        """Builds normalized options from central Config instance."""
        root = get_root_dir(project_root)
        dots = cfg.version.count(".")
        version_str = (
            f"{cfg.version}.0"
            if dots == 2
            else (f"{cfg.version}.0.0" if dots == 1 else cfg.version)
        )

        exe_ext = ".exe" if sys.platform == "win32" else ""
        exe_name = f"{cfg.cli_name}{exe_ext}"

        target_pkg = cfg.commands_pkg.split(".")[0]
        locales = get_locales_dir(target_pkg)
        locales_path = locales if locales.exists() else None

        icon = cfg.build.get("icon")
        icon_path = (root / icon) if icon and (root / icon).is_file() else None

        return cls(
            entry_point=root / cfg.build["entry_point"],
            dist_dir=root / cfg.build.get("output_dir", "dist"),
            exe_name=exe_name,
            version_str=version_str,
            commands_pkg=cfg.commands_pkg,  # ej. "app.commands" (solo comandos)
            locales_dir=locales_path,
            company_name=cfg.build.get("company_name", ""),
            title=cfg.title,
            description=cfg.description,
            copyright=cfg.copyright,
            icon_path=icon_path,
            extra_files=cfg.build.get("files", []),
        )