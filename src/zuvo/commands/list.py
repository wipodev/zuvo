"""
Audits and displays the status of command files against project configuration.
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from zuvo.core.config import Config, get_config
from zuvo.i18n import t
from zuvo.utils.paths import (
    get_root_dir,
    resolve_entry_commands,
    scan_command_files,
)

# Internal fallback console instance
_default_console = Console()

HELP = "cmd_list_help"
ARGS = []


def run(
    args=None,
    console: Console | None = None,
    config: Config | None = None,
    project_root: Path | str | None = None,
) -> None:
    """
    Lists registered commands per CLI app and performs structural auditing against the workspace.

    Args:
        args: Parsed CLI arguments namespace.
        console (Console | None): Rich Console instance for output rendering.
        config (Config | None): Override Config instance.
        project_root (Path | str | None): Root directory override.
    """
    out = console or _default_console
    cfg = config or get_config()
    root = get_root_dir(project_root)

    # 1. Resolve target commands directory
    rel_commands_dir = resolve_entry_commands(cfg.commands_pkg)
    abs_commands_dir = root / rel_commands_dir

    # 2. Discover physical python command files grouped by subfolder ('root', 'app1', etc.)
    discovered_files = scan_command_files(abs_commands_dir)

    out.print()
    out.print(
        Panel(
            f"[bold cyan]📋 {t('cmd_list_title_audit')}[/bold cyan]\n"
            f"[dim]{t('cmd_list_label_target_dir')}:[/dim] [yellow]{rel_commands_dir}[/yellow]",
            border_style="cyan",
            expand=False,
        )
    )

    # Track matched physical command files as (category, command_name)
    matched_physical_files: set[tuple[str, str]] = set()
    commands_dict: dict[str, list[str]] = (
        cfg.commands_config if isinstance(cfg.commands_config, dict) else {}
    )

    # 3. Render audit tables for each registered application
    for app_name, cmd_list in commands_dict.items():
        if not isinstance(cmd_list, list):
            continue

        table = Table(
            title=f"[bold bold_magenta]{t('cmd_list_table_title_app', app=app_name)}[/bold bold_magenta]",
            show_header=True,
            header_style="bold magenta",
            expand=False,
        )
        table.add_column(t("cmd_list_col_status"), justify="center", width=10)
        table.add_column(t("cmd_list_col_command"), style="cyan", width=20)
        table.add_column(t("cmd_list_col_file"), style="white")
        table.add_column(t("cmd_list_col_details"), style="dim")

        app_files = discovered_files.get(app_name, [])
        root_files = discovered_files.get("root", [])

        for cmd_name in cmd_list:
            if cmd_name in app_files:
                # Priority 1: Modular path (commands/app_name/cmd_name.py)
                matched_physical_files.add((app_name, cmd_name))
                status = "[bold green]✔ OK[/bold green]"
                details = t("cmd_list_desc_ok")
                file_rel_path = str(rel_commands_dir / app_name / f"{cmd_name}.py")
            elif cmd_name in root_files:
                # Priority 2: Flat path fallback (commands/cmd_name.py)
                matched_physical_files.add(("root", cmd_name))
                status = "[bold green]✔ OK[/bold green]"
                details = t("cmd_list_desc_ok")
                file_rel_path = str(rel_commands_dir / f"{cmd_name}.py")
            else:
                # Missing file error
                status = "[bold red]✖ ERR[/bold red]"
                details = t("cmd_list_desc_missing_file")
                file_rel_path = str(rel_commands_dir / app_name / f"{cmd_name}.py")

            table.add_row(status, cmd_name, file_rel_path, details)

        out.print(table)
        out.print()

    # 4. Check for orphan/unregistered python files
    orphan_rows: list[tuple[str, str]] = []  # (cmd_name, relative_path_str)

    for category, cmd_stems in discovered_files.items():
        for cmd_stem in cmd_stems:
            if (category, cmd_stem) not in matched_physical_files:
                if category == "root":
                    file_path = str(rel_commands_dir / f"{cmd_stem}.py")
                else:
                    file_path = str(rel_commands_dir / category / f"{cmd_stem}.py")

                orphan_rows.append((cmd_stem, file_path))

    if orphan_rows:
        orphan_rows.sort(key=lambda x: x[0])  # Sort orphans by command name
        table_orphans = Table(
            title=f"[bold yellow]⚠️  {t('cmd_list_table_title_unregistered')}[/bold yellow]",
            show_header=True,
            header_style="bold yellow",
            expand=False,
        )
        table_orphans.add_column(t("cmd_list_col_status"), justify="center", width=10)
        table_orphans.add_column(t("cmd_list_col_command"), style="cyan", width=20)
        table_orphans.add_column(t("cmd_list_col_file"), style="white")
        table_orphans.add_column(t("cmd_list_col_details"), style="dim")

        for cmd_name, file_rel_path in orphan_rows:
            status = "[bold yellow]⚠ WARN[/bold yellow]"
            details = t("cmd_list_desc_unregistered")
            table_orphans.add_row(status, cmd_name, file_rel_path, details)

        out.print(table_orphans)
        out.print()