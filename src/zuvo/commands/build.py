"""
Orchestrates application build processes using configured or specified compilers.
"""

import pprint
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from zuvo.compiler.builder import BuildOptions
from zuvo.compiler.nuitka import build_nuitka
from zuvo.compiler.pyinstaller import build_pyinstaller
from zuvo.compiler.pypi import build_pypi
from zuvo.core.config import Config, get_config
from zuvo.i18n import t

_default_console = Console()

HELP = "cmd_build_help"

ARGS = [
    {
        "flags": ["-c", "--compiler"],
        "type": str,
        "choices": ["pyinstaller", "nuitka", "pypi"],
        "help": "cmd_build_arg_compiler_help",
    },
    {
        "flags": ["-e", "--entry"],
        "type": str,
        "help": "cmd_build_arg_entry_help",
    },
    {
        "flags": ["-o", "--output"],
        "type": str,
        "help": "cmd_build_arg_output_help",
    },
]


def _generate_compiled_config(cfg: Config, root: Path) -> Path:
    """
    Generates static compiled configuration module before triggering build.

    Args:
        cfg (Config): Current active project configuration.
        root (Path): Active project root directory.

    Returns:
        Path: Path to generated compiled configuration file.
    """
    config_dict = cfg.to_dict()
    formatted_dict = pprint.pformat(config_dict, indent=4)

    generated_code = (
        '"""\n'
        "Auto-generated configuration for frozen/compiled binary.\n"
        '"""\n'
        "from zuvo.core.config import Config\n\n"
        f"COMPILED_CONFIG = Config.from_dict({formatted_dict})\n"
    )

    target_dir = root / "src" / "zuvo" / "core"
    target_dir.mkdir(parents=True, exist_ok=True)

    target_file = target_dir / "compiled_config.py"
    target_file.write_text(generated_code, encoding="utf-8")

    return target_file


def run(
    args,
    console: Console | None = None,
    config: Config | None = None,
    project_root: Path | str | None = None,
) -> None:
    """
    Executes build orchestration based on project configuration and CLI arguments.

    Args:
        args: Parsed arguments from argument parser.
        console (Console | None): Rich Console instance for output rendering (useful for testing).
        config (Config | None): Override Config instance (useful for testing).
        project_root (Path | str | None): Override project root directory (useful for testing).
    """
    out = console or _default_console
    cfg = config or get_config()
    root = Path(project_root) if project_root else Path.cwd()

    selected_compiler = (
        getattr(args, "compiler", None)
        or cfg.build.get("compiler", "pypi")
    ).lower()

    if getattr(args, "entry", None):
        cfg.build["entry_point"] = args.entry

    if getattr(args, "output", None):
        cfg.build["output_dir"] = args.output

    out.print(
        Panel(
            f"[bold cyan]🔨 {t('cmd_build_start_title', name=cfg.name)}[/bold cyan]\n"
            f"[dim]{t('cmd_build_compiler_label')}:[/dim] [yellow]{selected_compiler.upper()}[/yellow]\n"
            f"[dim]{t('cmd_build_version_label')}:[/dim] [green]v{cfg.version}[/green]",
            border_style="cyan",
            expand=False,
        )
    )

    compiled_cfg_path: Path | None = None
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=out,
        ) as progress:
            task = progress.add_task(
                description=f"[cyan]{t('cmd_build_generating_config')}[/cyan]",
                total=None,
            )
            compiled_cfg_path = _generate_compiled_config(cfg, root)
            progress.update(
                task,
                description=f"[green]✔ {t('cmd_build_config_generated')}[/green]",
            )

        out.print(
            f"[bold green]✔[/bold green] [dim]{t('cmd_build_config_saved')}:[/dim] [white]{compiled_cfg_path.relative_to(root)}[/white]"
        )

        opts = BuildOptions.from_config(cfg, project_root=root)

        success = False
        if selected_compiler == "nuitka":
            success = build_nuitka(opts=opts, config=cfg, console=out, project_root=root)
        elif selected_compiler == "pyinstaller":
            success = build_pyinstaller(opts=opts, config=cfg, console=out, project_root=root)
        elif selected_compiler == "pypi":
            success = build_pypi(opts=opts, config=cfg, console=out, project_root=root)
        else:
            out.print(
                f"[bold red]❌ {t('cmd_build_err_invalid_compiler', compiler=selected_compiler)}[/bold red]"
            )
            success = False

        if not success:
            sys.exit(1)

    finally:
        if compiled_cfg_path and compiled_cfg_path.exists():
            try:
                compiled_cfg_path.unlink()
            except OSError:
                pass