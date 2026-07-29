"""
Initializes a new Zuvo CLI project by generating a pyproject.toml configuration file.
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from zuvo.i18n import t

console = Console()

# i18n / Help Key definition
HELP = "cmd_init_help"

ARGS = [
    {
        "flags": ["-y", "--yes"],
        "action": "store_true",
        "help": "cmd_init_arg_yes_help",
    }
]


def _ask(prompt_text: str, default_val: str) -> str:
    """Helper to prompt the user using Rich with a styled default value."""
    formatted_prompt = f"[bold cyan]{prompt_text}[/bold cyan]"
    return Prompt.ask(formatted_prompt, default=default_val, console=console)


def _build_toml_content(data: dict) -> str:
    """Builds a formatted pyproject.toml content string."""
    return f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{data['name']}"
version = "{data['version']}"
description = "{data['description']}"
authors = [
    {{ name = "{data['author']}" }}
]
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "zuvo",
]

# ==============================================================================
# CONFIGURACIÓN DE ZUVO CLI
# ==============================================================================

[tool.zuvo]
type = "{data['type']}"
title = "{data['title']}"
executable_name = "{data['executable_name']}"
main = "{data['main']}"
commands_dir = "{data['commands_dir']}"
locales_dir = "{data['locales_dir']}"

[tool.zuvo.commands]
default = []

[tool.zuvo.scripts]
dev = "python {data['main']}"
"""


def run(args):
    """Executes the project initialization wizard or creates defaults if -y is provided."""
    skip_prompts = getattr(args, "yes", False)
    cwd_name = Path.cwd().name.lower().replace(" ", "-") or "zuvo-app"

    console.print()
    console.print(
        Panel(
            "[bold magenta]🚀 Zuvo CLI Initializer[/bold magenta]\n"
            f"[dim]Mode:[/dim] [yellow]{'Automatic (-y)' if skip_prompts else 'Interactive Wizard'}[/yellow]",
            border_style="magenta",
            expand=False,
        )
    )

    # Configuración por defecto
    config_data = {
        "name": cwd_name,
        "version": "0.1.0",
        "description": "A modern CLI application built with Zuvo",
        "author": "",
        "type": "standard",
        "title": cwd_name.replace("-", " ").title(),
        "executable_name": cwd_name,
        "main": "src/app/main.py",
        "commands_dir": "src/app/commands",
        "locales_dir": "locales",
    }

    # Si no es automático (-y), se ejecuta el asistente interactivo
    if not skip_prompts:
        console.print(
            "[dim]Press ENTER to accept the default values shown in brackets.[/dim]\n"
        )

        config_data["name"] = _ask("Project name", config_data["name"])
        config_data["version"] = _ask("Version", config_data["version"])
        config_data["description"] = _ask("Description", config_data["description"])
        config_data["author"] = _ask("Author", config_data["author"])

        # Muestra el selector rápido de tipo de aplicación
        config_data["type"] = Prompt.ask(
            "[bold cyan]Application Type[/bold cyan]",
            choices=["standard", "module"],
            default="standard",
            console=console,
        )

        config_data["executable_name"] = _ask(
            "Executable name", config_data["executable_name"]
        )
        config_data["commands_dir"] = _ask(
            "Commands directory", config_data["commands_dir"]
        )
        config_data["locales_dir"] = _ask(
            "Locales directory", config_data["locales_dir"]
        )

    target_path = Path.cwd() / "pyproject.toml"

    # Verificación de sobreescritura
    if target_path.exists() and not skip_prompts:
        overwrite = Prompt.ask(
            "\n[bold red]⚠️  pyproject.toml already exists. Overwrite?[/bold red]",
            choices=["y", "n"],
            default="n",
            console=console,
        )
        if overwrite.lower() != "y":
            console.print("[yellow]Aborted initialization.[/yellow]\n")
            return

    # Escribir el archivo pyproject.toml
    toml_content = _build_toml_content(config_data)
    target_path.write_text(toml_content, encoding="utf-8")

    # Resumen de resultados
    table = Table(
        title="Project Configuration Summary",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Property", style="bold yellow", width=20)
    table.add_column("Value", style="white")

    for key, val in config_data.items():
        table.add_row(key, str(val) if val else "[dim]none[/dim]")

    console.print()
    console.print(table)
    console.print(
        "\n[bold green]✔[/bold green] [white]Successfully generated [/white][bold cyan]pyproject.toml[/bold cyan]!\n"
    )