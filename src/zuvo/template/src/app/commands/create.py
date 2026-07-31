"""
Creates a new resource within the project workspace.

---
ZUVO COMMAND STRUCTURE OVERVIEW:
1. Module Docstring (above): Serves as the fallback description for the command 
   if no `HELP` variable or i18n translation key is found.
2. HELP (optional): Defines the description/help text or i18n translation key.
3. ARGS (optional): List of dictionaries specifying positional arguments, flags, 
   and type constraints parsed by argparse.
4. run(...) (required): Main execution entry point invoked when the command is called.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Internal fallback console instance if no custom console is passed during execution.
_default_console = Console()

# ZUVO CONFIG: Command Description / Help Text
# Can be a literal string or an i18n translation key.
# Defaults to the module docstring if omitted.
HELP = "cmd_create_help"

# ZUVO CONFIG: CLI Arguments & Flags Definition
# Demonstrates required parameters (`required=True`), type validation (`type=str`), 
# short/long flags, and boolean options (`action="store_true"`).
ARGS = [
    {
        "flags": ["-n", "--name"],
        "type": str,
        "required": True,
        "help": "cmd_create_arg_name_help",  # Literal string or i18n translation key
    },
    {
        "flags": ["--force"],
        "action": "store_true",
        "help": "cmd_create_arg_force_help",  # Literal string or i18n translation key
    },
]


# ZUVO ENTRY POINT: Command Execution Handler
# Invoked by Zuvo's dynamic command dispatcher.
# Parameters:
# - `args`: Namespace holding values for defined arguments (`args.name`, `args.force`).
# - `console` (optional): Rich Console instance injected by the runner for output rendering.
def run(args, console: Console | None = None):
    """Generates the requested project resource based on input flags."""
    # Use the injected Rich console or fall back to the default instance
    out = console or _default_console

    # Access mandatory and optional CLI argument values
    resource_name = args.name
    force_mode = getattr(args, "force", False)

    # --- Command Implementation Logic ---
    out.print(
        Panel(
            f"[bold blue]Creating Resource:[/bold blue] [bold yellow]{resource_name}[/bold yellow]",
            border_style="blue",
            expand=False,
        )
    )

    # Summary Table Output
    table = Table(
        title="Configuration Details",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Property", style="cyan", width=18)
    table.add_column("Value", style="white")

    table.add_row("Resource Name", resource_name)
    table.add_row(
        "Force Overwrite",
        "[red]True[/red]" if force_mode else "[green]False[/green]",
    )

    out.print(table)
    out.print(
        f"\n[bold green]✔[/bold green] Resource '[bold white]{resource_name}[/bold white]' initialized successfully.\n"
    )