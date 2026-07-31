"""
Creates a new Zuvo CLI project workspace using the standard template.
"""

import shutil
from pathlib import Path
from rich.console import Console

from zuvo.commands import init
from zuvo.i18n import t

_default_console = Console()

HELP = "cmd_create_help"

ARGS = [
    {
        "flags": ["-n", "--name"],
        "type": str,
        "required": True,
        "help": "cmd_create_arg_name_help",
    },
    {
        "flags": ["-y", "--yes"],
        "action": "store_true",
        "help": "cmd_create_arg_yes_help",
    },
]


def run(args, console: Console | None = None) -> None:
    """Creates directory structure, delegates metadata setup to init, and copies template files."""
    out = console or _default_console

    project_name = args.name
    target_dir = Path.cwd() / project_name

    if target_dir.exists() and any(target_dir.iterdir()):
        out.print(
            f"\n[bold red]❌ {t('cmd_create_err_dir_not_empty')}:[/bold red] [yellow]{target_dir}[/yellow]\n"
        )
        return

    target_dir.mkdir(parents=True, exist_ok=True)

    init_result = init.run(args, console=out, project_root=target_dir)

    if not init_result:
        out.print(f"[yellow]{t('cmd_create_aborted')}[/yellow]\n")
        return

    commands_pkg, _ = init_result
    root_pkg_name = commands_pkg.split(".")[0]

    template_dir = Path(__file__).resolve().parent.parent / "template"
    src_template = template_dir / "src" / "app"

    dest_pkg_dir = target_dir / "src" / root_pkg_name

    shutil.copytree(src_template, dest_pkg_dir)

    for template_file in template_dir.iterdir():
        if template_file.name == "src":
            continue
        if template_file.is_file():
            shutil.copy2(template_file, target_dir / template_file.name)
        elif template_file.is_dir():
            shutil.copytree(template_file, target_dir / template_file.name)

    out.print(
        f"[bold green]✔[/bold green] [white]{t('cmd_create_success_prefix')}[/white] "
        f"[bold cyan]{project_name}[/bold cyan] [white]({root_pkg_name})[/white]\n"
    )