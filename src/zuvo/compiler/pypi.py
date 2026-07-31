"""
PyPI wheel and source distribution builder module.
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from zuvo.compiler.builder import BuildOptions
from zuvo.core.config import Config, get_config
from zuvo.i18n import t
from zuvo.utils.exec import run_system_command
from zuvo.utils.paths import get_root_dir

_default_console = Console()


def _build_pypi_flags(opts: BuildOptions) -> list[str]:
    """
    Generates pure CLI arguments list for PyPA 'build' execution.
    
    Args:
        opts (BuildOptions): Configured build options.

    Returns:
        list[str]: Command line arguments for subprocess execution.
    """
    return [
        sys.executable,
        "-m",
        "build",
        "--outdir",
        str(opts.dist_dir),
    ]


def build_pypi(
    opts: BuildOptions | None = None,
    config: Config | None = None,
    console: Console | None = None,
    project_root: Path | str | None = None,
) -> bool:
    """
    Executes PyPI wheel and source distribution packaging using run_system_command.

    Args:
        opts (BuildOptions | None): Pre-configured BuildOptions instance.
        config (Config | None): Active project configuration instance.
        console (Console | None): Rich Console instance for output logging.
        project_root (Path | str | None): Root directory of the project.

    Returns:
        bool: True if packaging succeeds, False otherwise.
    """
    out = console or _default_console
    cfg = config or get_config()
    root = get_root_dir(project_root)

    options = opts or BuildOptions.from_config(cfg, project_root=root)

    # 1. UI Panel Header
    out.print()
    out.print(
        Panel(
            f"[bold magenta]📦 {t('build_pypi_title')}[/bold magenta]\n"
            f"[dim]{cfg.name} v{cfg.version}[/dim]",
            border_style="magenta",
            expand=False,
        )
    )

    # 2. Get CLI command flags
    cmd = _build_pypi_flags(options)

    # 3. Setup execution environment
    src_dir = root / "src"
    env = os.environ.copy()
    if src_dir.exists():
        env["PYTHONPATH"] = str(src_dir) + os.pathsep + env.get("PYTHONPATH", "")

    # 4. Execution using Rich status and run_system_command
    out.print(f"[bold cyan]🛠️  {t('build_packaging_status')}[/bold cyan]")
    out.print(Rule(style="dim"))

    try:
        with out.status(
            f"[bold green]{t('build_pypi_running')}[/bold green]", spinner="dots"
        ):
            run_system_command(cmd, cwd=root, env=env, console=out)

        out.print(Rule(style="dim"))
        out.print(
            f"\n[bold green]✔ {t('build_pypi_success_msg', path=str(options.dist_dir))}[/bold green]\n"
        )
        return True
    except Exception as err:
        out.print(Rule(style="dim"))
        out.print(f"\n[bold red]❌ {t('build_failed_msg')}: {err}[/bold red]\n")
        return False