import argparse
import sys
from rich.console import Console

from zuvo.core.errors import ExitCode, handle_cli_error
from zuvo.i18n import t
from zuvo.system_cmds import help as sys_help
from zuvo.system_cmds import version as sys_version

_default_console = Console(stderr=True)


def _register_command_args(
    parser: argparse.ArgumentParser,
    args_def: list[dict],
    raw_argv: list[str],
) -> None:
    """Processes and injects a module's declarative ARGS list into the parser."""
    valid_flags = {"-h", "--help", "-v", "--version"}
    for arg in args_def:
        valid_flags.update(arg.get("flags", []))

    has_unknown_flag = any(
        token.startswith("-") and token.split("=")[0] not in valid_flags 
        for token in raw_argv
    )
    is_asking_help = any(flag in raw_argv for flag in ("-h", "--help"))

    should_relax_required = is_asking_help or has_unknown_flag

    for arg in args_def:
        flags = arg.get("flags", [])
        if not flags:
            continue

        arg_copy = arg.copy()
        if should_relax_required and "required" in arg_copy:
            arg_copy["required"] = False

        kwargs = {k: v for k, v in arg_copy.items() if k != "flags"}
        parser.add_argument(*flags, **kwargs)


def _build_parser(
    commands_map: dict[str, object],
    invoked_as: str,
    raw_argv: list[str],
    console: Console | None = None,
) -> argparse.ArgumentParser:
    """Builds and configures the complete structure of the ArgumentParser."""
    parser = argparse.ArgumentParser(
        prog=invoked_as,
        add_help=False,
        allow_abbrev=False,
    )

    # Error handler for the main parser
    parser.error = lambda msg: handle_cli_error(
        msg, commands_map, invoked_as, console=console
    )

    # Global flags
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-v", "--version", action="store_true")

    # Subcommand container
    subparsers = parser.add_subparsers(dest="subcommand", metavar="<command>")

    for cmd_name, cmd_module in commands_map.items():
        subparser = subparsers.add_parser(cmd_name, add_help=False)
        subparser.add_argument("-h", "--help", action="store_true")

        # Error handler for this specific subcommand
        subparser.error = lambda msg: handle_cli_error(
            msg, commands_map, invoked_as, console=console
        )

        args_def = getattr(cmd_module, "ARGS", [])
        if isinstance(args_def, list) and args_def:
            _register_command_args(subparser, args_def, raw_argv)

    return parser


def _handle_global_flags(args: argparse.Namespace, console: Console | None = None) -> bool:
    """
    Intercepts global flags or commands such as help and version.
    Returns True if the request was processed and interrupted the normal flow.
    """
    out = console or _default_console

    # 1. Version Interception
    if args.version or args.subcommand == "version":
        sys_version.run(args, console=out)
        sys.exit(int(ExitCode.SUCCESS))

    # 2. General Help Interception
    if (args.help and not args.subcommand) or args.subcommand == "help" or not args.subcommand:
        sys_help.run(args, console=out)
        sys.exit(int(ExitCode.SUCCESS))

    return False


def _dispatch_command(
    args: argparse.Namespace,
    commands_map: dict[str, object],
    console: Console | None = None,
) -> None:
    """Dispatches execution to the corresponding subcommand."""
    out = console or _default_console
    selected_cmd = commands_map.get(args.subcommand)

    if selected_cmd and not (hasattr(selected_cmd, "run") and callable(selected_cmd.run)):
        err_msg = t("cli_error_missing_run_fn", cmd=args.subcommand)
        handle_cli_error(
            raw_message=err_msg,
            commands_map=commands_map,
            invoked_as=getattr(args, "_invoked_as", "app"),
            code_override=ExitCode.INVALID_COMMAND_MODULE,
            console=out,
        )

    # If explicit help was requested for a subcommand (e.g., app create -h)
    if getattr(args, "help", False):
        setattr(args, "_target_cmd", selected_cmd)
        sys_help.run(args, console=out)
        sys.exit(int(ExitCode.SUCCESS))

    try:
        selected_cmd.run(args)
    except Exception as e:
        err_msg = t("cli_error_execution", cmd=args.subcommand, error=e)
        out.print(f"[bold red]{err_msg}[/bold red]")
        sys.exit(int(ExitCode.COMMAND_EXECUTION_ERROR))


def build_parser_and_run(
    commands_map: dict[str, object],
    invoked_as: str,
    argv: list[str] | None = None,
    console: Console | None = None,
) -> None:
    """Main orchestrator of the CLI lifecycle."""
    raw_argv = argv if argv is not None else sys.argv[1:]
    parser = _build_parser(commands_map, invoked_as, raw_argv, console=console)

    try:
        args = parser.parse_args(raw_argv)
    except SystemExit as e:
        sys.exit(e.code)

    setattr(args, "_commands_map", commands_map)
    setattr(args, "_invoked_as", invoked_as)

    _handle_global_flags(args, console=console)
    _dispatch_command(args, commands_map, console=console)