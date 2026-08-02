"""
CLI command to publish pre-built package artifacts to PyPI or TestPyPI.
"""

import importlib.util
import os
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

from zuvo.core.config import Config, get_config
from zuvo.i18n import t
from zuvo.utils.exec import run_system_command
from zuvo.utils.paths import get_root_dir

_default_console = Console()

HELP = "cmd_publish_help"

ARGS = [
    {
        "flags": ["--repository", "-r"],
        "help": "cmd_publish_arg_repository_help",
        "choices": ["pypi", "testpypi"],
        "default": "testpypi",
        "type": str,
    },
]

# Direct API token management links
TOKEN_URLS = {
    "pypi": "https://pypi.org/manage/account/token/",
    "testpypi": "https://test.pypi.org/manage/account/token/",
}


def _has_pypirc_credentials(repository: str) -> bool:
    """
    Checks if credentials for the target repository exist in ~/.pypirc.

    Args:
        repository (str): Target repository section name.

    Returns:
        bool: True if section exists and contains password/token, False otherwise.
    """
    pypirc_path = Path.home() / ".pypirc"
    if not pypirc_path.exists():
        return False

    config = ConfigParser()
    config.read(pypirc_path, encoding="utf-8")

    if config.has_section(repository):
        return bool(config.get(repository, "password", fallback=None))
    return False


def _save_token_to_pypirc(repository: str, token: str) -> None:
    """
    Saves or updates API token credentials in the user's ~/.pypirc file,
    ensuring [distutils] stays at the top and registers all present sections.

    Args:
        repository (str): Target repository ('pypi' or 'testpypi').
        token (str): API token string starting with 'pypi-'.
    """
    pypirc_path = Path.home() / ".pypirc"
    config = ConfigParser()

    if pypirc_path.exists():
        config.read(pypirc_path, encoding="utf-8")

    if not config.has_section(repository):
        config.add_section(repository)

    if repository == "testpypi":
        config.set(repository, "repository", "https://test.pypi.org/legacy/")
    elif repository == "pypi":
        config.set(repository, "repository", "https://upload.pypi.org/legacy/")

    config.set(repository, "username", "__token__")
    config.set(repository, "password", token)

    # Collect all repository sections (excluding distutils itself)
    all_repositories = [sec for sec in config.sections() if sec != "distutils"]
    if repository not in all_repositories:
        all_repositories.append(repository)

    # Rebuild a clean reordered ConfigParser
    clean_config = ConfigParser()
    clean_config.add_section("distutils")
    clean_config.set(
        "distutils",
        "index-servers",
        "\n" + "\n".join(sorted(all_repositories)),
    )

    for sec in config.sections():
        if sec == "distutils":
            continue
        clean_config.add_section(sec)
        for key, value in config.items(sec):
            clean_config.set(sec, key, value)

    with open(pypirc_path, "w", encoding="utf-8") as f:
        clean_config.write(f)


def _ensure_credentials(repository: str, console: Console) -> None:
    """
    Ensures publishing credentials exist, offering interactive prompt and auto-save.

    Args:
        repository (str): Target repository name.
        console (Console): Rich console instance.
    """
    if os.environ.get("TWINE_PASSWORD") or os.environ.get("TWINE_AUTH_TOKEN"):
        return

    if _has_pypirc_credentials(repository):
        return

    token_url = TOKEN_URLS.get(repository, TOKEN_URLS["pypi"])

    console.print(
        Panel(
            f"[bold yellow]⚠️  {t('cmd_publish_warn_no_credentials', repo=repository)}[/bold yellow]\n\n"
            f"[dim]{t('cmd_publish_hint_get_token')}:[/dim]\n"
            f"[bold cyan]{token_url}[/bold cyan]",
            border_style="yellow",
            expand=False,
        )
    )

    token = Prompt.ask(
        f"[bold green]🔑 {t('cmd_publish_prompt_enter_token')}[/bold green]",
        password=True,
        console=console,
    ).strip()

    if not token:
        console.print(f"[bold red]❌ {t('cmd_publish_err_empty_token')}[/bold red]\n")
        sys.exit(1)

    _save_token_to_pypirc(repository, token)
    console.print(
        f"[bold green]✔ {t('cmd_publish_msg_token_saved', path='~/.pypirc')}[/bold green]\n"
    )


def run(
    args: Any = None,
    console: Console | None = None,
    config: Config | None = None,
    project_root: Path | str | None = None,
) -> None:
    """
    Publishes built artifacts from the dist/ directory using twine.

    Args:
        args: Parsed CLI arguments namespace.
        console (Console | None): Rich Console instance for output.
        config (Config | None): Override Config instance.
        project_root (Path | str | None): Root directory override.
    """
    out = console or _default_console
    cfg = config or get_config()
    root = get_root_dir(project_root)
    dist_dir = root / "dist"

    target_repository = getattr(args, "repository", "testpypi")

    out.print()

    # 1. Validate twine availability
    if importlib.util.find_spec("twine") is None:
        out.print(
            Panel(
                f"[bold red]❌ {t('cmd_publish_err_twine_missing')}[/bold red]\n"
                f"[dim]{t('cmd_publish_hint_install_twine')}[/dim]",
                border_style="red",
                expand=False,
            )
        )
        sys.exit(1)

    # 2. Validate existence of distribution artifacts
    if not dist_dir.is_dir() or not any(dist_dir.iterdir()):
        out.print(
            Panel(
                f"[bold red]❌ {t('cmd_publish_err_no_dist')}[/bold red]\n"
                f"[dim]{t('cmd_publish_hint_run_build')}[/dim]",
                border_style="red",
                expand=False,
            )
        )
        sys.exit(1)

    try:
        # 3. Check and assist with credentials if missing
        _ensure_credentials(target_repository, out)

        # 4. Inform publishing strategy
        out.print(
            Panel(
                f"[bold cyan]🚀 {t('cmd_publish_title_publishing')}[/bold cyan]\n"
                f"[dim]{t('cmd_publish_label_package')}:[/dim] [yellow]{cfg.name}[/yellow]\n"
                f"[dim]{t('cmd_publish_label_version')}:[/dim] [magenta]v{cfg.version}[/magenta]\n"
                f"[dim]{t('cmd_publish_label_repository')}:[/dim] [bold yellow]{target_repository.upper()}[/bold yellow]",
                border_style="cyan",
                expand=False,
            )
        )

        # Build twine command with non-interactive flag safety
        cmd = [
            sys.executable,
            "-m",
            "twine",
            "upload",
            "--non-interactive",
            "--repository",
            target_repository,
            str(dist_dir / "*"),
        ]

        out.print(f"[bold cyan]🛠️  {t('cmd_publish_status_executing')}[/bold cyan]")
        out.print(Rule(style="dim"))

        with out.status(
            f"[bold green]{t('cmd_publish_running_twine', repo=target_repository)}[/bold green]",
            spinner="dots",
        ):
            run_system_command(cmd, cwd=root, console=out)

        out.print(Rule(style="dim"))
        out.print(
            f"\n[bold green]✔ {t('cmd_publish_success', repo=target_repository)}[/bold green]\n"
        )

    except KeyboardInterrupt:
        out.print(f"\n[dim]{t('cmd_publish_msg_cancelled')}[/dim]\n")
        sys.exit(130)

    except Exception as err:
        out.print(Rule(style="dim"))
        out.print(
            f"\n[bold red]❌ {t('cmd_publish_failed', repo=target_repository)}: {err}[/bold red]\n"
        )
        sys.exit(1)