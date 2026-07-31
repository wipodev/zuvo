"""
Orchestrates application packaging processes using configured or specified packagers.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from zuvo.core.config import Config, get_config
from zuvo.i18n import t
from zuvo.packager.innosetup import package_innosetup

_default_console = Console()

HELP = "cmd_package_help"

ARGS = [
    {
        "flags": ["-t", "--type"],
        "type": str,
        "choices": ["inno", "appimage", "dmg"],
        "help": "cmd_package_arg_type_help",
    },
]


def run(
    args,
    console: Console | None = None,
    config: Config | None = None,
    project_root: Path | str | None = None,
) -> None:
    """
    Executes packaging orchestration based on project configuration and CLI arguments.

    Args:
        args: Parsed arguments from argument parser.
        console (Console | None): Rich Console instance for output rendering.
        config (Config | None): Override Config instance.
        project_root (Path | str | None): Override project root directory.
    """
    out = console or _default_console
    cfg = config or get_config()
    root = Path(project_root) if project_root else Path.cwd()

    selected_type = getattr(args, "type", None)
    if not selected_type:
        if sys.platform.startswith("win"):
            selected_type = "inno"
        elif sys.platform.startswith("linux"):
            selected_type = "appimage"
        elif sys.platform.startswith("darwin"):
            selected_type = "dmg"
        else:
            out.print(
                f"[bold red]❌ {t('cmd_package_err_unsupported_os', os=sys.platform)}[/bold red]"
            )
            sys.exit(1)

    selected_type = selected_type.lower()

    out.print(
        Panel(
            f"[bold cyan]📦 {t('cmd_package_start_title', name=cfg.name)}[/bold cyan]\n"
            f"[dim]{t('cmd_package_type_label')}:[/dim] [yellow]{selected_type.upper()}[/yellow]\n"
            f"[dim]{t('cmd_package_version_label')}:[/dim] [green]v{cfg.version}[/green]",
            border_style="cyan",
            expand=False,
        )
    )

    success = False
    if selected_type == "inno":
        if not sys.platform.startswith("win"):
            out.print(
                f"[bold red]❌ {t('cmd_package_err_win_only', packager='Inno Setup')}[/bold red]"
            )
            sys.exit(1)

        success = package_innosetup(
            config=cfg,
            console=out,
            project_root=root,
        )
    else:
        out.print(
            f"[bold red]❌ {t('cmd_package_err_invalid_type', type=selected_type)}[/bold red]"
        )
        success = False

    if not success:
        sys.exit(1)