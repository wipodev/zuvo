"""
Initializes a new Zuvo CLI project by generating a pyproject.toml configuration file.
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from zuvo.i18n import t

_default_console = Console()

HELP = "cmd_init_help"

ARGS = [
    {
        "flags": ["-y", "--yes"],
        "action": "store_true",
        "help": "cmd_init_arg_yes_help",
    }
]


def _ask(prompt_text: str, default_val: str, console: Console) -> str:
    """
    Helper to prompt the user using Rich with a styled default value.
    """
    formatted_prompt = f"[bold cyan]{prompt_text}[/bold cyan]"
    return Prompt.ask(formatted_prompt, default=default_val, console=console)


def _build_toml_content(data: dict) -> str:
    """
    Builds a formatted pyproject.toml content string with descriptive comments.
    """
    authors_block = (
        f'\nauthors = [\n    {{ name = "{data["author"]}" }}\n]'
        if data["author"]
        else ""
    )

    return f"""# ==============================================================================
# Build System Configuration
# ==============================================================================
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# ==============================================================================
# Standard Project Metadata (PEP 621)
# ==============================================================================
[project]
name = "{data['name']}"
version = "{data['version']}"
description = "{data['description']}"{authors_block}
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "zuvo",
]

# CLI Entrypoint mapping: executable_name = "package.module:function"
[project.scripts]
{data['cli_name']} = "{data['entry_point']}"

# ==============================================================================
# Zuvo Framework Settings
# ==============================================================================
[tool.zuvo]
# Display title used in CLI headers, panels, and help outputs
title = "{data['title']}"

# Legal copyright notice displayed in application footers or metadata
copyright = "{data['copyright']}"

# Python package dot-path where command modules reside (e.g., app.commands)
commands_pkg = "{data['commands_pkg']}"

# Default command configurations and subcommand aliases
[tool.zuvo.commands]
{data['cli_name']} = []

# Packaging & Compilation Settings (PyInstaller)
[tool.zuvo.build]
cli_name = "{data['cli_name']}"        # Name of the output executable binary
entry_point = "{data['entry_point']}"   # Main Python script path used as compilation entry point
compiler = "pyinstaller"      # Compiler engine used for standalone binary creation
company_name = "{data['author']}"  # Metadata publisher/company name
icon = ""                      # Path to .ico or binary icon file
output_dir = "dist"            # Target directory for compiled binaries

# Windows Installer Settings (Inno Setup)
[tool.zuvo.inno]
inno_path = "C:\\\\Program Files (x86)\\\\Inno Setup 6\\\\ISCC.exe" # Path to ISCC compiler
app_publisher_url = ""         # Publisher homepage URL
license_file = ""              # Path to license file (.txt or .rtf)
default_dir_name = "{data['cli_name']}"  # Default installation folder under Program Files
output_base_filename = "{data['cli_name']}-Setup" # Generated setup installer executable name
"""


def run(
    args,
    console: Console | None = None,
    project_root: Path | str | None = None,
) -> None:
    """
    Executes the project initialization wizard or creates defaults if -y is provided.

    Args:
        args: Parsed arguments from argument parser.
        console (Console | None): Rich Console instance for output rendering.
        project_root (Path | str | None): Override project root directory.
    """
    out = console or _default_console
    root = Path(project_root) if project_root else Path.cwd()
    skip_prompts = getattr(args, "yes", False)
    cwd_name = root.name.lower().replace(" ", "-") or "cli-app"

    mode_text = t("cmd_init_mode_auto") if skip_prompts else t("cmd_init_mode_wizard")

    out.print()
    out.print(
        Panel(
            f"[bold magenta]🚀 {t('cmd_init_panel_title')}[/bold magenta]\n"
            f"[dim]{t('cmd_init_mode_label')}:[/dim] [yellow]{mode_text}[/yellow]",
            border_style="magenta",
            expand=False,
        )
    )

    config_data = {
        "name": cwd_name,
        "version": "0.1.0",
        "description": t("cmd_init_default_description"),
        "author": "",
        "cli_name": cwd_name,
        "title": cwd_name.replace("-", " ").title(),
        "copyright": "Copyright © 2026",
        "entry_point": "app.main:main",
        "commands_pkg": "app.commands",
    }

    if not skip_prompts:
        out.print(
            f"[dim]{t('cmd_init_prompt_enter_hint')}[/dim]\n"
        )

        config_data["name"] = _ask(t("cmd_init_prompt_name"), config_data["name"], out)
        config_data["version"] = _ask(t("cmd_init_prompt_version"), config_data["version"], out)
        config_data["description"] = _ask(
            t("cmd_init_prompt_description"), config_data["description"], out
        )
        config_data["author"] = _ask(t("cmd_init_prompt_author"), config_data["author"], out)
        config_data["cli_name"] = _ask(
            t("cmd_init_prompt_cli_name"), config_data["name"], out
        )
        config_data["entry_point"] = _ask(
            t("cmd_init_prompt_entry_point"), config_data["entry_point"], out
        )
        config_data["title"] = _ask(t("cmd_init_prompt_title"), config_data["title"], out)
        config_data["commands_pkg"] = _ask(
            t("cmd_init_prompt_commands_pkg"), config_data["commands_pkg"], out
        )

    target_path = root / "pyproject.toml"

    if target_path.exists() and not skip_prompts:
        overwrite = Prompt.ask(
            f"\n[bold red]⚠️  {t('cmd_init_overwrite_warning')}[/bold red]",
            choices=["y", "n"],
            default="n",
            console=out,
        )
        if overwrite.lower() != "y":
            out.print(f"[yellow]{t('cmd_init_aborted')}[/yellow]\n")
            return

    toml_content = _build_toml_content(config_data)
    target_path.write_text(toml_content, encoding="utf-8")

    table = Table(
        title=t("cmd_init_table_title"),
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column(t("cmd_init_table_col_property"), style="bold yellow", width=20)
    table.add_column(t("cmd_init_table_col_value"), style="white")

    for key, val in config_data.items():
        table.add_row(key, str(val) if val else f"[dim]{t('cmd_init_val_none')}[/dim]")

    out.print()
    out.print(table)
    out.print(
        f"\n[bold green]✔[/bold green] [white]{t('cmd_init_success_prefix')} [/white]"
        f"[bold cyan]pyproject.toml[/bold cyan]!\n"
    )