import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from zuvo.compiler.builder import BuildOptions
from zuvo.core.config import Config, get_config
from zuvo.i18n import t
from zuvo.utils.exec import run_system_command
from zuvo.utils.paths import get_root_dir

_default_console = Console()


def _build_flags(opts: BuildOptions, root: Path) -> list[str]:
    """Generates pure CLI arguments list for Nuitka compilation."""
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        f"--output-dir={opts.dist_dir}",
        f"--output-filename={opts.exe_name}",
        "--remove-output",
        "--assume-yes-for-downloads",
        # SOLUCIÓN: Solo incluimos el paquete de comandos dinámicos, NO el paquete raíz entero
        f"--include-package={opts.commands_pkg}",
    ]

    # Traducciones externas (se copian como datos directos fuera del binario)
    if opts.locales_dir:
        locales_dir = opts.locales_dir
        rel_locales = (
            locales_dir.relative_to(root)
            if locales_dir.is_relative_to(root)
            else locales_dir
        )
        cmd.append(f"--include-data-dir={root / rel_locales}=locales")

    # Metadatos del binario
    if opts.company_name:
        cmd.append(f"--company-name={opts.company_name}")
    if opts.title:
        cmd.append(f"--product-name={opts.title}")
    if opts.description:
        cmd.append(f"--file-description={opts.description}")
    if opts.copyright:
        cmd.append(f"--copyright={opts.copyright}")

    cmd.extend(
        [
            f"--file-version={opts.version_str}",
            f"--product-version={opts.version_str}",
        ]
    )

    if opts.icon_path and sys.platform == "win32":
        cmd.append(f"--windows-icon-from-ico={opts.icon_path}")

    # User Defined Assets Inclusion
    for src_path, dest_rel in opts.assets.items():
        if src_path.is_dir():
            cmd.append(f"--include-data-dir={src_path}={dest_rel}")
        elif src_path.is_file():
            cmd.append(f"--include-data-files={src_path}={dest_rel}")

    cmd.append(str(opts.entry_point))
    return cmd


def build_nuitka(
    opts: BuildOptions | None = None,
    config: Config | None = None,
    console: Console | None = None,
    project_root: Path | str | None = None,
) -> bool:
    """
    Executes Nuitka compilation using pre-configured BuildOptions.
    """
    out = console or _default_console
    cfg = config or get_config()
    root = get_root_dir(project_root)

    options = opts or BuildOptions.from_config(cfg, project_root=root)

    if not options.entry_point.is_file():
        out.print(
            f"[bold red]❌ {t('build_err_missing_entry', path=str(options.entry_point))}[/bold red]"
        )
        return False

    # 1. Interfaz de usuario
    out.print()
    out.print(
        Panel(
            f"[bold magenta]🚀 {t('build_nuitka_title')}[/bold magenta]\n"
            f"[dim]{cfg.name} v{cfg.version}[/dim]",
            border_style="magenta",
            expand=False,
        )
    )

    # 2. Obtener lista pura de argumentos del builder
    cmd = _build_flags(options, root)

    # 3. Entorno de ejecución
    src_dir = root / "src"
    env = os.environ.copy()
    if src_dir.exists():
        env["PYTHONPATH"] = str(src_dir) + os.pathsep + env.get("PYTHONPATH", "")

    # 4. Ejecución con spinner Rich
    out.print(f"[bold cyan]🛠️  {t('build_compiling_status')}[/bold cyan]")
    out.print(Rule(style="dim"))

    try:
        with out.status(
            f"[bold green]{t('build_nuitka_running')}[/bold green]", spinner="dots"
        ):
            run_system_command(cmd, cwd=root, env=env, console=out)

        out.print(Rule(style="dim"))
        out.print(
            f"\n[bold green]✔ {t('build_success_msg', path=str(options.dist_dir))}[/bold green]\n"
        )
        return True
    except Exception as err:
        out.print(Rule(style="dim"))
        out.print(f"\n[bold red]❌ {t('build_failed_msg')}: {err}[/bold red]\n")
        return False