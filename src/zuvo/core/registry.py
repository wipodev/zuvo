import argparse
import sys
from rich.console import Console

from zuvo.system_cmds import version as sys_version
from zuvo.system_cmds import help as sys_help
from zuvo.core.errors import handle_cli_error, ExitCode
from zuvo.i18n import t

console = Console(stderr=True)


def _register_command_args(parser: argparse.ArgumentParser, args_def: list[dict]) -> None:
    """Processes and injects a module's declarative ARGS list into the parser."""
    is_asking_help = any(flag in sys.argv for flag in ("-h", "--help"))

    for arg in args_def:
        flags = arg.get("flags", [])
        if not flags:
            continue

        arg_copy = arg.copy()
        if is_asking_help and "required" in arg_copy:
            arg_copy["required"] = False

        kwargs = {k: v for k, v in arg_copy.items() if k != "flags"}
        parser.add_argument(*flags, **kwargs)


def _build_parser(commands_map: dict[str, object], invoked_as: str) -> argparse.ArgumentParser:
    """Builds and configures the complete structure of the ArgumentParser."""
    parser = argparse.ArgumentParser(
        prog=invoked_as,
        add_help=False,
        allow_abbrev=False
    )

    # Error handler for the main parser
    parser.error = lambda msg: handle_cli_error(msg, commands_map, invoked_as)

    # Global flags
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-v", "--version", action="store_true")

    # Subcommand container
    subparsers = parser.add_subparsers(dest="subcommand", metavar="<command>")

    for cmd_name, cmd_module in commands_map.items():
        subparser = subparsers.add_parser(cmd_name, add_help=False)
        subparser.add_argument("-h", "--help", action="store_true")

        # Error handler for this specific subcommand
        subparser.error = lambda msg: handle_cli_error(msg, commands_map, invoked_as)

        args_def = getattr(cmd_module, "ARGS", [])
        if isinstance(args_def, list) and args_def:
            _register_command_args(subparser, args_def)

    return parser


def _handle_global_flags(args: argparse.Namespace) -> bool:
    """
    Intercepts global flags or commands such as help and version.
    Returns True if the request was processed and interrupted the normal flow.
    """
    # 1. Version Interception
    if args.version or args.subcommand == "version":
        sys_version.run(args)
        sys.exit(int(ExitCode.SUCCESS))

    # 2. General Help Interception
    if (args.help and not args.subcommand) or args.subcommand == "help" or not args.subcommand:
        sys_help.run(args)
        sys.exit(int(ExitCode.SUCCESS))

    return False


def _dispatch_command(args: argparse.Namespace, commands_map: dict[str, object]) -> None:
    """Dispatches execution to the corresponding subcommand."""
    selected_cmd = commands_map.get(args.subcommand)

    if selected_cmd and not (hasattr(selected_cmd, "run") and callable(selected_cmd.run)):
        err_msg = t("cli_error_missing_run_fn", cmd=args.subcommand)
        handle_cli_error(
            raw_message=err_msg, 
            commands_map=commands_map, 
            invoked_as=getattr(args, "_invoked_as", "app"), 
            code_override=ExitCode.INVALID_COMMAND_MODULE
        )

    # If explicit help was requested for a subcommand (e.g., app create -h)
    if getattr(args, "help", False):
        setattr(args, "_target_cmd", selected_cmd)
        sys_help.run(args)
        sys.exit(int(ExitCode.SUCCESS))

    try:
        selected_cmd.run(args)
    except Exception as e:
        err_msg = t("cli_error_execution", cmd=args.subcommand, error=e)
        console.print(f"[bold red]{err_msg}[/bold red]")
        sys.exit(int(ExitCode.COMMAND_EXECUTION_ERROR))


def build_parser_and_run(commands_map: dict[str, object], invoked_as: str) -> None:
    """Main orchestrator of the CLI lifecycle."""
    parser = _build_parser(commands_map, invoked_as)

    try:
        args = parser.parse_args()
    except SystemExit as e:
        sys.exit(e.code)

    setattr(args, "_commands_map", commands_map)
    setattr(args, "_invoked_as", invoked_as)

    _handle_global_flags(args)
    _dispatch_command(args, commands_map)