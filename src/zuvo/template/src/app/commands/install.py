"""
Installs all necessary environment dependencies.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

console = Console()

# Optional: Override description for i18n key or custom text
HELP = "cmd_install_help"

ARGS = [
    {
        "flags": ["--dev"],
        "action": "store_true",
        "help": "cmd_install_arg_dev_help"
    }
]


def run(args):
    """Executes the environment setup and dependency installation routine."""
    is_dev = getattr(args, "dev", False)
    mode_text = "Development" if is_dev else "Production"

    console.print(
        Panel(
            f"[bold cyan]Starting Installation Process[/bold cyan]\n"
            f"[dim]Environment Mode:[/dim] [yellow]{mode_text}[/yellow]",
            border_style="cyan",
            expand=False,
        )
    )

    # Simulated installation process with Rich Spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Resolving packages...", total=None)
        time.sleep(1)

        progress.update(task, description="Downloading dependencies...")
        time.sleep(1)

        progress.update(task, description="Linking binaries...")
        time.sleep(0.8)

    console.print("[bold green]✔[/bold green] [white]Dependencies successfully installed![/white]\n")