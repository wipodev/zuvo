"""
Generates structured documentation for registered CLI commands.
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from zuvo.core.config import Config, get_config
from zuvo.core.inspector import AppDoc, extract_command_doc
from zuvo.core.runner import load_command_modules
from zuvo.docs.renderers import get_renderer
from zuvo.i18n import i18n, t
from zuvo.utils.paths import get_root_dir

_default_console = Console()

HELP = "cmd_docs_help"

ARGS = [
    {
        "flags": ["--out", "-o"],
        "help": "cmd_docs_arg_out",
        "default": None,
        "type": str,
    },
    {
        "flags": ["--format", "-f"],
        "help": "cmd_docs_arg_format",
        "choices": ["markdown", "json"],
        "default": "markdown",
        "type": str,
    },
    {
        "flags": ["--lang", "-l"],
        "help": "cmd_docs_arg_lang",
        "default": "auto",
        "type": str,
    },
    {
        "flags": ["--app", "-a"],
        "help": "cmd_docs_arg_app",
        "default": None,
        "type": str,
    },
]


def run(
    args: Any = None,
    console: Console | None = None,
    config: Config | None = None,
    project_root: Path | str | None = None,
) -> None:
    """
    Main execution handler for 'zuvo docs'.
    """
    out = console or _default_console
    cfg = config or get_config()
    root = get_root_dir(project_root)

    target_lang = getattr(args, "lang", "auto")
    original_locale = i18n.current_lang

    if target_lang and target_lang != "auto":
        i18n.set_language(target_lang)

    out.print()
    
    try:
        commands_dict: dict[str, list[str]] = (
            cfg.commands_config if isinstance(cfg.commands_config, dict) else {}
        )
        target_app_filter = getattr(args, "app", None)
        fmt = getattr(args, "format", "markdown")
        apps_docs: list[AppDoc] = []
        total_commands_count = 0

        with out.status(
            f"[bold cyan]{t('cmd_docs_status_generating', default='Generating CLI documentation...')}[/bold cyan]",
            spinner="dots",
        ):
            for app_name, cmd_list in commands_dict.items():
                if not isinstance(cmd_list, list):
                    continue

                if target_app_filter and app_name != target_app_filter:
                    continue

                commands_map = load_command_modules(
                    cmd_list,
                    cfg.commands_pkg,
                    app_name=app_name,
                    project_root=root,
                )

                cmd_docs = [
                    extract_command_doc(cmd_name, mod, cfg.commands_pkg, app_name)
                    for cmd_name, mod in commands_map.items()
                    if mod is not None
                ]

                total_commands_count += len(cmd_docs)
                apps_docs.append(AppDoc(app_name=app_name, commands=cmd_docs))

            renderer = get_renderer(fmt)
            content = renderer.render(apps_docs)

            default_filename = "COMMANDS.json" if fmt == "json" else "COMMANDS.md"
            out_filename = getattr(args, "out", None) or default_filename
            output_path = root / out_filename

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")

        # --- Summary Display ---
        header_text = (
            f"[bold magenta]📚 {cfg.title or 'Zuvo'}[/bold magenta] "
            f"[bold white]Documentation Generator[/bold white]"
        )
        out.print(Panel(header_text, expand=False, border_style="magenta"))

        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_column("Property", style="bold cyan")
        summary_table.add_column("Value")

        summary_table.add_row(
            t("docs_prop_output", default="Output File"),
            f"[bold green]{out_filename}[/bold green]",
        )
        summary_table.add_row(
            t("docs_prop_format", default="Format"),
            f"[bold yellow]{fmt.upper()}[/bold yellow]",
        )
        summary_table.add_row(
            t("docs_prop_apps", default="Applications Processed"),
            str(len(apps_docs)),
        )
        summary_table.add_row(
            t("docs_prop_commands", default="Total Commands"),
            str(total_commands_count),
        )

        out.print(summary_table)
        out.print(Rule(style="dim"))
        out.print(
            f" [bold green]✔[/bold green] {t('cmd_docs_msg_success', path=out_filename)}\n"
        )

    finally:
        if target_lang and target_lang != "auto":
            i18n.set_language(original_locale)