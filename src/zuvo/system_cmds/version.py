from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from zuvo.core import project
from zuvo.i18n import t

console = Console()


def run(args=None) -> None:
    """
    Displays the project version and metadata report using Rich for formatted output.
    """
    header_text = (
        f"[bold magenta]{project.TITLE}[/bold magenta] "
        f"[bold green]v{project.VERSION}[/bold green]"
    )
    
    console.print()
    console.print(Panel(header_text, expand=False, border_style="dim"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="bold cyan")
    table.add_column("Value")

    table.add_row(t("version_prop_project"), project.NAME)
    table.add_row(t("version_prop_executable"), project.EXECUTABLE_NAME)
    
    if project.DESCRIPTION:
        table.add_row(t("version_prop_description"), project.DESCRIPTION)
        
    if project.AUTHOR:
        table.add_row(t("version_prop_author"), f"[dim]{project.AUTHOR}[/dim]")
        
    if project.COPYRIGHT:
        table.add_row(t("version_prop_copyright"), f"[dim]{project.COPYRIGHT}[/dim]")

    console.print(table)
    console.print("\n[dim]----------------------------------------------------------------------[/dim]\n")