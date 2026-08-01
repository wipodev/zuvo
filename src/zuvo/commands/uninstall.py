"""
Uninstalls Python packages from the environment and removes dependencies from pyproject.toml.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from zuvo.core.config import Config, get_config
from zuvo.deps.manager import (
    read_pyproject,
    remove_dependencies,
    write_pyproject,
)
from zuvo.i18n import t
from zuvo.utils.exec import run_system_command
from zuvo.utils.paths import get_root_dir

_default_console = Console()

HELP = "cmd_uninstall_help"

ARGS = [
    {
        "flags": ["packages"],
        "type": str,
        "nargs": "+",
        "help": "cmd_uninstall_arg_packages_help",
    },
    {
        "flags": ["-d", "--dev"],
        "action": "store_true",
        "help": "cmd_uninstall_arg_dev_help",
    },
]


def run(
    args,
    console: Console | None = None,
    config: Config | None = None,
    project_root: Path | str | None = None,
) -> None:
    """
    Uninstalls packages from the environment and updates pyproject.toml.

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

    dep_type_label = (
        t("cmd_uninstall_type_dev") if is_dev else t("cmd_uninstall_type_prod")
    )

    out.print(
        Panel(
            f"[bold red]🗑️  {t('cmd_uninstall_title_uninstalling')}[/bold red]\n"
            f"[dim]{t('cmd_uninstall_label_packages')}:[/dim] [yellow]{', '.join(packages)}[/yellow]\n"
            f"[dim]{t('cmd_uninstall_label_type')}:[/dim] [magenta]{dep_type_label}[/magenta]",
            border_style="red",
            expand=False,
        )
    )

    # Build pip command to uninstall selected packages non-interactively (-y / --yes)
    cmd = [sys.executable, "-m", "pip", "uninstall", "-y"] + packages

    out.print(f"[bold red]🛠️  {t('cmd_uninstall_status_executing')}[/bold red]")
    out.print(Rule(style="dim"))

    try:
        with out.status(
            f"[bold yellow]{t('cmd_uninstall_running_pip')}[/bold yellow]",
            spinner="dots",
        ):
            success = run_system_command(cmd, cwd=root, console=out)

        out.print(Rule(style="dim"))

        # Update pyproject.toml only upon successful uninstallation
        if success:
            if pyproject_path.exists():
                doc = read_pyproject(pyproject_path)
                if remove_dependencies(doc, packages, is_dev=is_dev):
                    write_pyproject(pyproject_path, doc)

            out.print(
                f"\n[bold green]✔ {t('cmd_uninstall_success_packages')}[/bold green]\n"
            )
        else:
            out.print(
                f"\n[bold red]❌ {t('cmd_uninstall_failed_packages')}[/bold red]\n"
            )
            sys.exit(1)

    except Exception as err:
        out.print(Rule(style="dim"))
        out.print(
            f"\n[bold red]❌ {t('cmd_uninstall_failed_packages')}: {err}[/bold red]\n"
        )
        sys.exit(1)