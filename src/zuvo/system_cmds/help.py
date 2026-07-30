from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from zuvo.core.config import Config, get_config
from zuvo.i18n import t

_default_console = Console()


def _get_clean_doc(cmd_module: object) -> str:
    """Extracts a command description from HELP, docstrings, or default value."""
    help_attr = getattr(cmd_module, "HELP", None)
    if help_attr:
        return t(str(help_attr).strip())

    doc = None
    if hasattr(cmd_module, "run"):
        doc = getattr(cmd_module.run, "__doc__", None)
    if not doc:
        doc = getattr(cmd_module, "__doc__", None)

    if not doc:
        return t("help_no_description")

    return str(doc).strip()


# --- Render Helpers: General Help ---

def _build_commands_table(commands_map: dict) -> Table:
    """Creates the available commands table for general help."""
    table = Table(show_header=True, header_style="bold cyan", box=None, pad_edge=False)
    table.add_column(t("help_col_command"), style="bold green", width=16)
    table.add_column(t("help_col_description"), style="white")

    for cmd_name, cmd_module in commands_map.items():
        doc = _get_clean_doc(cmd_module)
        table.add_row(cmd_name, doc)

    return table


def _build_global_options_table() -> Table:
    """Creates the global options table (-h, -v)."""
    options_table = Table(show_header=True, header_style="bold cyan", box=None, pad_edge=False)
    options_table.add_column(t("help_col_option"), style="bold yellow", width=18)
    options_table.add_column(t("help_col_description"), style="white")

    options_table.add_row("-h, --help", t("help_opt_help_desc"))
    options_table.add_row("-v, --version", t("help_opt_version_desc"))

    return options_table


def _build_general_header_panel(invoked_as: str, cfg: Config | None = None) -> Panel:
    """Constructs the top welcome/usage panel for general CLI help."""
    cfg = cfg or get_config()

    content = Text()
    content.append(t("help_usage_label"), style="bold white")
    syntax_text = t("help_usage_syntax_general", prog=invoked_as)
    content.append(f"{syntax_text}\n", style="bold gold1")

    if cfg.description:
        content.append(f"\n{cfg.description}", style="dim")

    panel_title = (f"[bold magenta]🚀 {cfg.title or 'CLI'}[/bold magenta]")
    panel_subtitle = (f"[italic gray]v{cfg.version or '0.0.0'}[/italic gray]")

    return Panel(
        content,
        title=panel_title,
        subtitle=panel_subtitle,
        border_style="magenta",
        expand=False,
    )


def _show_general_help(commands_map: dict, invoked_as: str, console: Console, cfg: Config | None = None) -> None:
    """Renders the general CLI help menu."""
    console.print()
    console.print(_build_general_header_panel(invoked_as, cfg=cfg))

    console.print(f"\n[bold cyan]{t('help_header_commands')}[/bold cyan]")
    console.print(_build_commands_table(commands_map))

    console.print(f"\n[bold cyan]{t('help_header_options')}[/bold cyan]")
    console.print(_build_global_options_table())

    console.print(f"\n[bold gray]{t('help_example_label')}[/bold gray]")
    console.print(f"  [dim]$[/dim] [green]{invoked_as}[/green] [yellow]help[/yellow]\n")


# --- Render Helpers: Subcommand Help ---

def _build_command_options_table(args_def: list[dict]) -> Table:
    """Creates the options/flags table specific to a subcommand."""
    table = Table(show_header=True, header_style="bold cyan", box=None, pad_edge=False)
    table.add_column(t("help_col_option_flag"), style="bold yellow", width=22)
    table.add_column(t("help_col_description"), style="white")

    for arg in args_def:
        flags = ", ".join(arg.get("flags", []))
        help_raw = arg.get("help")
        help_text = t(help_raw) if help_raw else t("help_no_description")

        if arg.get("required"):
            required_tag = t("help_required_tag")
            help_text += f" [bold red]{required_tag}[/bold red]"

        table.add_row(flags, help_text)

    return table


def _generate_command_example(cmd_name: str, args_def: list[dict], invoked_as: str) -> str:
    """Dynamically generates a string example for subcommand usage."""
    tokens = [f"[green]{invoked_as}[/green]", f"[yellow]{cmd_name}[/yellow]"]

    if not args_def:
        return " ".join(tokens)

    first_arg = args_def[0]
    flags = first_arg.get("flags", [])

    if flags:
        long_flag = next((f for f in flags if f.startswith("--")), None)
        short_flag = next((f for f in flags if f.startswith("-")), None)
        display_flag = short_flag or flags[0]

        if display_flag.startswith("-"):
            tokens.append(f"[cyan]{display_flag}[/cyan]")
            action = first_arg.get("action", "")
            if action not in ("store_true", "store_false"):
                ref_flag = long_flag or display_flag
                clean_var = ref_flag.lstrip("-").replace("-", "_")
                tokens.append(f"[magenta]<{clean_var}>[/magenta]")
        else:
            tokens.append(f"[magenta]<{display_flag}>[/magenta]")

    return " ".join(tokens)


def _show_command_help(cmd_name: str, cmd_module: object, invoked_as: str, console: Console) -> None:
    """Renders detailed help for a specific subcommand."""
    doc = _get_clean_doc(cmd_module)
    args_def = getattr(cmd_module, "ARGS", [])

    content = Text()
    content.append(t("help_usage_label"), style="bold white")
    cmd_syntax = t("help_usage_syntax_command", prog=invoked_as, cmd=cmd_name)
    content.append(f"{cmd_syntax}\n\n", style="bold gold1")
    content.append(doc, style="white")

    panel_title = t("help_panel_cmd_title", cmd=cmd_name)

    console.print()
    console.print(
        Panel(
            content,
            title=f"[bold magenta]{panel_title}[/bold magenta]",
            border_style="magenta",
            expand=False,
        )
    )

    if args_def:
        console.print(f"\n[bold cyan]{t('help_header_command_options')}[/bold cyan]")
        console.print(_build_command_options_table(args_def))

    example_str = _generate_command_example(cmd_name, args_def, invoked_as)
    console.print(f"\n[bold gray]{t('help_example_label')}[/bold gray]")
    console.print(f"  [dim]$[/dim] {example_str}\n")


# --- Main Orchestrator ---

def run(args=None, console: Console | None = None, config: Config | None = None) -> None:
    """Main help orchestrator."""
    out = console or _default_console
    cfg = config or get_config()

    commands_map = getattr(args, "_commands_map", {})
    invoked_as = getattr(args, "_invoked_as", cfg.cli_name or "app")
    target_cmd = getattr(args, "_target_cmd", None)
    subcmd_name = getattr(args, "subcommand", None)

    if target_cmd:
        if not subcmd_name:
            subcmd_name = getattr(target_cmd, "NAME", None)

        _show_command_help(subcmd_name, target_cmd, invoked_as, out)
    else:
        _show_general_help(commands_map, invoked_as, out, cfg)