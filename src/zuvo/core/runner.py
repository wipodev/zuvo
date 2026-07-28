import sys, importlib 
from pathlib import Path
from rich.console import Console

from zuvo.core.project import EXECUTABLE_NAME, APP_TYPE, COMMANDS_CONFIG
from zuvo.core.registry import build_parser_and_run
from zuvo.core.errors import ExitCode
from zuvo.i18n import t

console = Console(stderr=True)

def get_invocation_name() -> str:
    """
    Extracts the name of the invoked executable or entrypoint script.

    Returns:
        str: Cleaned name of the command context.
    """
    raw_name = Path(sys.argv[0]).stem
    if raw_name in ("__main__", "main"):
        return EXECUTABLE_NAME
    return raw_name

def load_command_modules(command_names: list[str], package_path: str) -> dict:
    """
    Dynamically imports command modules explicitly configured in project.json.

    Args:
        command_names (List[str]): List of command names to load.
        package_path (str): Base Python package import path.

    Returns:
        dict: Mapping of command names to imported module objects.
    """
    # Ensure current working directory is in sys.path to allow user app imports
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    commands = {}
    for cmd_name in command_names:
        module_path = f"{package_path}.{cmd_name}"
        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, "run") and callable(mod.run):
                commands[cmd_name] = mod
            else:
                msg = t("main_warn_cmd_missing_run", cmd=cmd_name)
                console.print(msg)
        except ModuleNotFoundError as e:
            msg = t("main_warn_cmd_module_not_found", cmd=cmd_name, error=e)
            console.print(msg)
        except Exception as e:
            msg = t("main_warn_cmd_load_error", cmd=cmd_name, error=e)
            console.print(f"{msg} (Details: {e})")
    return commands

def run_app():
    """
    Bootstraps the active user CLI application.
    Resolves invocation context, imports declared user commands, and runs parser.
    """
    invoked_as = get_invocation_name()

    if APP_TYPE == "module":
        if invoked_as in COMMANDS_CONFIG:
            cmd_list = COMMANDS_CONFIG.get(invoked_as, [])
            package_path = f"src.app.commands.{invoked_as}"
        else:
            msg = t("main_err_unrecognized_context", invoked_as=invoked_as)
            console.print(msg)
            sys.exit(int(ExitCode.UNKNOWN_CONTEXT))
    else:
        cmd_list = COMMANDS_CONFIG if isinstance(COMMANDS_CONFIG, list) else []
        package_path = "src.app.commands"

    commands_map = load_command_modules(cmd_list, package_path)
    build_parser_and_run(commands_map, invoked_as)

if __name__ == "__main__":
    run_app()