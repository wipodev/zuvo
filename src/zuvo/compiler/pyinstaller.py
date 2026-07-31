import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from zuvo.compiler.builder import BuildOptions
from zuvo.compiler.version_info import generate_version_file
from zuvo.core.config import Config, get_config
from zuvo.i18n import t
from zuvo.utils.exec import run_system_command
from zuvo.utils.paths import get_root_dir

_default_console = Console()


def _build_flags(opts: BuildOptions, root: Path) -> tuple[list[str], Path | None]:
    """
    Constructs CLI flag arguments specifically for PyInstaller execution.

    Args:
        opts (BuildOptions): Normalized build configuration.
        root (Path): Active project root directory.

    Returns:
        tuple[list[str], Path | None]: Formatted arguments and path to temporary version file (if created).
    """
    sep = ";" if sys.platform == "win32" else ":"
    clean_name = opts.exe_name.removesuffix(".exe")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        f"--distpath={opts.dist_dir}",
        f"--name={clean_name}",
        # Target dynamic command modules without bundling the entire package
        f"--collect-submodules={opts.commands_pkg}",
    ]

    # External locales directory inclusion
    if opts.locales_dir:
        locales_dir = opts.locales_dir
        rel_locales = (
            locales_dir.relative_to(root)
            if locales_dir.is_relative_to(root)
            else locales_dir
        )
        cmd.append(f"--add-data={root / rel_locales}{sep}locales")

    if sys.platform == "win32":
        build_tmp_dir = root / "build"
        build_tmp_dir.mkdir(parents=True, exist_ok=True)
        version_file_path = build_tmp_dir / "version_info.txt"
        generate_version_file(opts, version_file_path)
        cmd.append(f"--version-file={version_file_path}")

    # Icon configuration
    if opts.icon_path:
        cmd.append(f"--icon={opts.icon_path}")

    # Additional extra data files
    for extra in opts.extra_files:
        if "=" in extra:
            src_f, dst_f = extra.split("=", 1)
            cmd.append(f"--add-data={src_f}{sep}{dst_f}")

    # Target entry point script
    cmd.append(str(opts.entry_point))
    return cmd, version_file_path


def build_pyinstaller(
    opts: BuildOptions | None = None,
    config: Config | None = None,
    console: Console | None = None,
    project_root: Path | str | None = None,
) -> bool:
    """
    Executes native compilation using PyInstaller based on BuildOptions.

    Args:
        opts (BuildOptions | None): Pre-built compilation options.
        config (Config | None): Active Config override.
        console (Console | None): Rich Console instance for UI output.
        project_root (Path | str | None): Custom project root override.
    """
    out = console or _default_console
    cfg = config or get_config()
    root = get_root_dir(project_root)

    options = opts or BuildOptions.from_config(cfg, project_root=root)

    if not options.entry_point.is_file():
        out.print(
            f"[bold red]❌ {t('build_err_missing_entry', path=str(options.entry_point))}[/bold red]"
        )
        return False

    # 1. Visual Panel Header
    out.print()
    out.print(
        Panel(
            f"[bold magenta]🚀 {t('build_pyinstaller_title')}[/bold magenta]\n"
            f"[dim]{cfg.name} v{cfg.version}[/dim]",
            border_style="magenta",
            expand=False,
        )
    )

    # 2. Build PyInstaller-specific flags
    cmd, version_file_path = _build_flags(options, root)

    # 3. Environment setup
    src_dir = root / "src"
    env = os.environ.copy()
    if src_dir.exists():
        env["PYTHONPATH"] = str(src_dir) + os.pathsep + env.get("PYTHONPATH", "")

    # 4. Execution with Rich spinner status
    out.print(f"[bold cyan]🛠️  {t('build_compiling_status')}[/bold cyan]")
    out.print(Rule(style="dim"))

    success = False
    try:
        with out.status(
            f"[bold green]{t('build_pyinstaller_running')}[/bold green]", spinner="dots"
        ):
            run_system_command(cmd, cwd=root, env=env, console=out)

        out.print(Rule(style="dim"))
        out.print(
            f"\n[bold green]✔ {t('build_success_msg', path=str(options.dist_dir))}[/bold green]\n"
        )
        success = True
    except Exception as err:
        out.print(Rule(style="dim"))
        out.print(f"\n[bold red]❌ {t('build_failed_msg')}: {err}[/bold red]\n")
        success = False
    finally:
        # Cleanup temporary version file
        if version_file_path and version_file_path.exists():
            try:
                version_file_path.unlink()
            except OSError:
                pass

    return success