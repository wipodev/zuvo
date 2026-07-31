"""
Initializes a new Zuvo CLI project by generating a pyproject.toml configuration file.
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from zuvo.i18n import t

# Default fallback console for standard CLI invocation
_default_console = Console()

# i18n Translation key for command help
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
compiler = "pyinstaller"      # Compiler engine used for standalone binary creation
company_name = "{data['author']}"  # Metadata publisher/company name
icon = ""                      # Path to .ico or binary icon file
files = []                     # Additional static data files or assets to bundle
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
        config (Config | None): Override Config instance.
        project_root (Path | str | None): Override project root directory.
    """
    out = console or _default_console
    root = Path(project_root) if project_root else Path.cwd()
    skip_prompts = getattr(args, "yes", False)
    cwd_name = root.name.lower().replace(" ", "-") or "cli-app"

    out.print()
    out.print(
        Panel(
            "[bold magenta]🚀 Zuvo CLI Initializer[/bold magenta]\n"
            f"[dim]Mode:[/dim] [yellow]{'Automatic (-y)' if skip_prompts else 'Interactive Wizard'}[/yellow]",
            border_style="magenta",
            expand=False,
        )
    )

    # Base configuration aligned with Config model defaults
    config_data = {
        "name": cwd_name,
        "version": "0.1.0",
        "description": "A modern CLI application built with Zuvo",
        "author": "",
        "cli_name": cwd_name,
        "title": cwd_name.replace("-", " ").title(),
        "copyright": "Copyright © 2026",
        "entry_point": "app.main:main",
        "commands_pkg": "app.commands",
    }

    # Interactive wizard mode
    if not skip_prompts:
        out.print(
            "[dim]Press ENTER to accept the default values shown in brackets.[/dim]\n"
        )

        config_data["name"] = _ask("Project name", config_data["name"], out)
        config_data["version"] = _ask("Version", config_data["version"], out)
        config_data["description"] = _ask(
            "Description", config_data["description"], out
        )
        config_data["author"] = _ask("Author", config_data["author"], out)
        config_data["cli_name"] = _ask(
            "CLI command name", config_data["name"], out
        )
        config_data["entry_point"] = _ask(
            "Entry point script (pkg.module:fn)", config_data["entry_point"], out
        )
        config_data["title"] = _ask("Application title", config_data["title"], out)
        config_data["commands_pkg"] = _ask(
            "Commands package", config_data["commands_pkg"], out
        )

    target_path = root / "pyproject.toml"

    # Overwrite check
    if target_path.exists() and not skip_prompts:
        overwrite = Prompt.ask(
            "\n[bold red]⚠️  pyproject.toml already exists. Overwrite?[/bold red]",
            choices=["y", "n"],
            default="n",
            console=out,
        )
        if overwrite.lower() != "y":
            out.print("[yellow]Aborted initialization.[/yellow]\n")
            return

    # Write generated content
    toml_content = _build_toml_content(config_data)
    target_path.write_text(toml_content, encoding="utf-8")

    # Output summary table
    table = Table(
        title="Project Configuration Summary",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Property", style="bold yellow", width=20)
    table.add_column("Value", style="white")

    for key, val in config_data.items():
        table.add_row(key, str(val) if val else "[dim]none[/dim]")

    out.print()
    out.print(table)
    out.print(
        "\n[bold green]✔[/bold green] [white]Successfully generated [/white][bold cyan]pyproject.toml[/bold cyan]!\n"
    )