from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

from zuvo.core.config import Config, get_config
from zuvo.i18n import t

_default_console = Console()


def run(args=None, console: Console | None = None, config: Config | None = None) -> None:
    """
    Displays the project version and metadata report using Rich for formatted output.
    """
    out = console or _default_console
    cfg = config or get_config()

    header_text = (
        f"[bold magenta]{cfg.title}[/bold magenta] "
        f"[bold green]v{cfg.version}[/bold green]"
    )

    out.print()
    out.print(Panel(header_text, expand=False, border_style="dim"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Property", style="bold cyan")
    table.add_column("Value")

    table.add_row(t("version_prop_project"), cfg.name)
    table.add_row(t("version_prop_executable"), cfg.cli_name)

    if cfg.description:
        table.add_row(t("version_prop_description"), cfg.description)

    if cfg.author:
        table.add_row(t("version_prop_author"), f"[dim]{cfg.author}[/dim]")

    copyright_text = cfg.build.get("copyright", "")
    if copyright_text:
        table.add_row(t("version_prop_copyright"), f"[dim]{copyright_text}[/dim]")

    out.print(table)
    
    out.print(Rule(style="dim"))