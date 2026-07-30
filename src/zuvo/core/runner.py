import importlib
from pathlib import Path
import sys
from rich.console import Console

from zuvo.core.errors import ExitCode
from zuvo.core.config import Config, set_config
from zuvo.core.registry import build_parser_and_run
from zuvo.i18n import i18n, t

try:
    from zuvo.core.compiled_config import COMPILED_CONFIG # type: ignore
except ImportError:
    COMPILED_CONFIG = None

_default_console = Console(stderr=True)


def get_invocation_name(argv_0: str | None = None, fallback: str = "app") -> str:
    """
    Extracts the name of the invoked executable or entrypoint script.

    Args:
        argv_0 (str | None): Optional raw invocation path for test injection.

    Returns:
        str: Cleaned name of the command context.
    """
    source = argv_0 if argv_0 is not None else (sys.argv[0] if sys.argv else "")
    raw_name = Path(source).stem if source else fallback

    if raw_name in ("__main__", "main", ""):
        return fallback
    return raw_name


def load_command_modules(
    command_names: list[str],
    package_path: str,
    project_root: Path | str | None = None,
    console: Console | None = None,
) -> dict[str, object]:
    """
    Dynamically imports command modules explicitly configured in pyproject.toml.

    Args:
        command_names (list[str]): List of command names to load.
        package_path (str): Base Python package import path.
        console (Console | None): Optional console for warnings/errors output.

    Returns:
        dict[str, object]: Mapping of command names to imported module objects.
    """
    out = console or _default_console

    # Ensure current working directory is in sys.path to allow user app imports
    root_path = str(Path(project_root).resolve()) if project_root else str(Path.cwd().resolve())
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

    commands = {}
    for cmd_name in command_names:
        module_path = f"{package_path}.{cmd_name}"
        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, "run") and callable(mod.run):
                commands[cmd_name] = mod
            else:
                msg = t("main_warn_cmd_missing_run", cmd=cmd_name)
                out.print(msg)
        except ModuleNotFoundError as e:
            msg = t("main_warn_cmd_module_not_found", cmd=cmd_name, error=e)
            out.print(msg)
        except Exception as e:
            msg = t("main_warn_cmd_load_error", cmd=cmd_name, error=e)
            out.print(f"{msg} (Details: {e})")

    return commands


def run_app(
    argv: list[str] | None = None,
    console: Console | None = None,
    locales_dir: Path | None = None,
    project_root: Path | str | None = None,
    config: Config | None = None,
) -> None:
    """
    Bootstraps the active user CLI application.
    Resolves invocation context, imports declared user commands, and runs parser.
    """
    out = console or _default_console
    raw_argv = argv if argv is not None else sys.argv[1:]
    argv_0 = sys.argv[0] if sys.argv else ""

    cfg = config or COMPILED_CONFIG or Config.load(project_root)
    set_config(cfg)

    target_locales = locales_dir or cfg.locales_dir
    if target_locales and target_locales.exists():
        i18n.set_locale_dir(target_locales)

    invoked_as = get_invocation_name(argv_0, cfg.executable_name)

    if cfg.app_type == "module":
        if invoked_as in cfg.commands_config:
            cmd_list = cfg.commands_config.get(invoked_as, [])
            package_path = f"{cfg.commands_pkg}.{invoked_as}"
        else:
            msg = t("main_err_unrecognized_context", invoked_as=invoked_as)
            out.print(msg)
            sys.exit(int(ExitCode.UNKNOWN_CONTEXT))
    else:
        cmd_list = cfg.commands_config.get("default", [])
        package_path = cfg.commands_pkg

    commands_map = load_command_modules(cmd_list, package_path, project_root=project_root, console=out)
    build_parser_and_run(commands_map, invoked_as, argv=raw_argv, console=out)


if __name__ == "__main__":
    run_app()