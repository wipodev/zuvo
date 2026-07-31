"""
Installs Python packages into the environment and manages dependencies in pyproject.toml.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from zuvo.core.config import Config, get_config
from zuvo.deps.manager import (
    add_dependencies,
    read_pyproject,
    write_pyproject,
)
from zuvo.i18n import t
from zuvo.utils.exec import run_system_command
from zuvo.utils.paths import get_root_dir

_default_console = Console()

HELP = "cmd_install_help"

ARGS = [
    {
        "flags": ["packages"],
        "type": str,
        "nargs": "*",
        "help": "cmd_install_arg_packages_help",
    },
    {
        "flags": ["-d", "--dev"],
        "action": "store_true",
        "help": "cmd_install_arg_dev_help",
    },
]


def run(
    args,
    console: Console | None = None,
    config: Config | None = None,
    project_root: Path | str | None = None,
) -> None:
    """
    Installs packages or restores project dependencies from pyproject.toml.

    Args:
        args: Parsed CLI arguments namespace.
        console (Console | None): Rich Console instance for output.
        config (Config | None): Override Config instance.
        project_root (Path | str | None): Root directory override.
    """
    out = console or _default_console
    cfg = config or get_config()
    root = get_root_dir(project_root)
    pyproject_path = root / "pyproject.toml"

    packages: list[str] = getattr(args, "packages", []) or []
    is_dev: bool = getattr(args, "dev", False)

    out.print()

    # 1. Direct Package Installation Mode
    if packages:
        dep_type_label = (
            t("cmd_install_type_dev") if is_dev else t("cmd_install_type_prod")
        )

        out.print(
            Panel(
                f"[bold cyan]📦 {t('cmd_install_title_installing')}[/bold cyan]\n"
                f"[dim]{t('cmd_install_label_packages')}:[/dim] [yellow]{', '.join(packages)}[/yellow]\n"
                f"[dim]{t('cmd_install_label_type')}:[/dim] [magenta]{dep_type_label}[/magenta]",
                border_style="cyan",
                expand=False,
            )
        )

        # Build pip command using --no-input for non-interactive execution
        cmd = [sys.executable, "-m", "pip", "install", "--no-input"] + packages

        out.print(f"[bold cyan]🛠️  {t('cmd_install_status_executing')}[/bold cyan]")
        out.print(Rule(style="dim"))

        try:
            with out.status(
                f"[bold green]{t('cmd_install_running_pip')}[/bold green]",
                spinner="dots",
            ):
                success = run_system_command(cmd, cwd=root, console=out)

            out.print(Rule(style="dim"))

            # Update pyproject.toml only upon successful installation
            if success:
                doc = read_pyproject(pyproject_path)
                if add_dependencies(doc, packages, is_dev=is_dev):
                    write_pyproject(pyproject_path, doc)

                out.print(
                    f"\n[bold green]✔ {t('cmd_install_success_packages')}[/bold green]\n"
                )
            else:
                out.print(
                    f"\n[bold red]❌ {t('cmd_install_failed_packages')}[/bold red]\n"
                )
                sys.exit(1)

        except Exception as err:
            out.print(Rule(style="dim"))
            out.print(
                f"\n[bold red]❌ {t('cmd_install_failed_packages')}: {err}[/bold red]\n"
            )
            sys.exit(1)

    # 2. Sync/Restore Project Dependencies Mode
    else:
        out.print(
            Panel(
                f"[bold cyan]🔄 {t('cmd_install_title_syncing')}[/bold cyan]\n"
                f"[dim]{cfg.title} v{cfg.version}[/dim]",
                border_style="cyan",
                expand=False,
            )
        )

        if not pyproject_path.exists():
            out.print(
                f"[bold red]❌ {t('cmd_install_err_missing_pyproject', path=str(pyproject_path))}[/bold red]\n"
            )
            sys.exit(1)

        cmd = [sys.executable, "-m", "pip", "install", "--no-input", "-e", "."]
        if is_dev:
            cmd[-1] = ".[dev]"

        out.print(f"[bold cyan]🛠️  {t('cmd_install_status_syncing')}[/bold cyan]")
        out.print(Rule(style="dim"))

        try:
            with out.status(
                f"[bold green]{t('cmd_install_running_sync')}[/bold green]",
                spinner="dots",
            ):
                success = run_system_command(cmd, cwd=root, console=out)

            out.print(Rule(style="dim"))

            if success:
                out.print(
                    f"\n[bold green]✔ {t('cmd_install_success_sync')}[/bold green]\n"
                )
            else:
                out.print(
                    f"\n[bold red]❌ {t('cmd_install_failed_sync')}[/bold red]\n"
                )
                sys.exit(1)

        except Exception as err:
            out.print(Rule(style="dim"))
            out.print(
                f"\n[bold red]❌ {t('cmd_install_failed_sync')}: {err}[/bold red]\n"
            )
            sys.exit(1)