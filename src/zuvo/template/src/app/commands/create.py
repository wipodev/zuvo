"""
Creates a new resource within the project workspace.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Optional: Override description for i18n key or custom text
HELP = "cmd_create_help"

ARGS = [
    {
        "flags": ["-n", "--name"],
        "type": str,
        "required": True,
        "help": "cmd_create_arg_name_help"
    },
    {
        "flags": ["--force"],
        "action": "store_true",
        "help": "cmd_create_arg_force_help"
    }
]


def run(args):
    """Generates the requested project resource based on input flags."""
    resource_name = args.name
    force_mode = getattr(args, "force", False)

    console.print(
        Panel(
            f"[bold blue]Creating Resource:[/bold blue] [bold yellow]{resource_name}[/bold yellow]",
            border_style="blue",
            expand=False,
        )
    )

    # Summary Table Output
    table = Table(title="Configuration Details", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", width=18)
    table.add_column("Value", style="white")

    table.add_row("Resource Name", resource_name)
    table.add_row("Force Overwrite", "[red]True[/red]" if force_mode else "[green]False[/green]")

    console.print(table)
    console.print(f"\n[bold green]✔[/bold green] Resource '[bold white]{resource_name}[/bold white]' initialized successfully.\n")