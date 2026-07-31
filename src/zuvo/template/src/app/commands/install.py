"""
Installs all necessary environment dependencies.

---
ZUVO COMMAND STRUCTURE OVERVIEW:
1. Module Docstring (above): Serves as the fallback description for the command 
   if no `HELP` variable or i18n translation key is found.
2. HELP (optional): Defines the description/help text or i18n translation key.
3. ARGS (optional): List of dictionaries specifying arguments and flags parsed 
   by argparse.
4. run(...) (required): Main execution entry point invoked when the command is called.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

# Internal fallback console instance if no custom console is passed during execution.
_default_console = Console()

# ZUVO CONFIG: Command Description / Help Text
# Can be a literal string (e.g., "Installs dependencies") or an i18n translation key.
# If omitted, Zuvo defaults to the module docstring at the top of the file.
HELP = "cmd_install_help"

# ZUVO CONFIG: CLI Arguments & Flags Definition
# List of dictionaries, where each entry represents an argument or flag passed to argparse.add_argument().
# Supported keys: "flags" (list), "action", "type", "default", "help", "nargs", "choices", etc.
ARGS = [
    {
        "flags": ["--dev"],
        "action": "store_true",
        "help": "cmd_install_arg_dev_help", # Literal string or i18n translation key
    }
]


# ZUVO ENTRY POINT: Command Execution Handler
# Zuvo dynamically imports this module and invokes `run(...)` when the command is executed.
# Parameters:
# - `args`: Parsed argparse namespace containing all flags and arguments defined in ARGS.
# - `console` (optional): Rich Console instance injected by the runner for standardized CLI rendering.
def run(args, console: Console | None = None):
    """Executes the environment setup and dependency installation routine."""
    # Use the injected Rich console or fall back to the default instance
    out = console or _default_console
    
    # Access arguments defined in ARGS via attributes on `args`
    is_dev = getattr(args, "dev", False)
    mode_text = "Development" if is_dev else "Production"

    # --- Command Implementation Logic ---
    out.print(
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

    out.print("[bold green]✔[/bold green] [white]Dependencies successfully installed![/white]\n")