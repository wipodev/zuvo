from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from zuvo.core import config
from zuvo.i18n import t

_default_console = Console()


def run(args=None, console: Console | None = None) -> None:
    """
    Displays the project version and metadata report using Rich for formatted output.
    """
    out = console or _default_console

    header_text = (
        f"[bold magenta]{config.TITLE}[/bold magenta] "
        f"[bold green]v{config.VERSION}[/bold green]"
    )

    out.print()
    out.print(Panel(header_text, expand=False, border_style="dim"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="bold cyan")
    table.add_column("Value")

    table.add_row(t("version_prop_project"), config.NAME)
    table.add_row(t("version_prop_executable"), config.EXECUTABLE_NAME)

    if config.DESCRIPTION:
        table.add_row(t("version_prop_description"), config.DESCRIPTION)

    if config.AUTHOR:
        table.add_row(t("version_prop_author"), f"[dim]{config.AUTHOR}[/dim]")

    if config.COPYRIGHT:
        table.add_row(t("version_prop_copyright"), f"[dim]{config.COPYRIGHT}[/dim]")

    out.print(table)
    out.print(
        "\n[dim]----------------------------------------------------------------------[/dim]\n"
    )