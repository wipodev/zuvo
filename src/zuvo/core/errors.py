import re
import sys
from argparse import Namespace
from enum import IntEnum
from rich.console import Console

from zuvo.core.config import Config, get_config
from zuvo.system_cmds import help as sys_help
from zuvo.i18n import t

_default_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# 1. Centralized Exit Code Table / Mapping
# ---------------------------------------------------------------------------
class ExitCode(IntEnum):
    SUCCESS = 0
    UNKNOWN_CONTEXT = 1
    UNKNOWN_COMMAND = 2
    COMMAND_EXECUTION_ERROR = 3
    INVALID_COMMAND_MODULE = 4
    MISSING_REQUIRED_ARG = 10
    UNKNOWN_FLAG = 11
    INVALID_ARG_TYPE = 12
    AMBIGUOUS_ARG = 13
    GENERIC_SYNTAX_ERROR = 20


# ---------------------------------------------------------------------------
# 2. Argparse Internal Message Parser to i18n
# ---------------------------------------------------------------------------
def parse_argparse_error(raw_message: str) -> tuple[ExitCode, str]:
    """
    Parses the native English message emitted by argparse
    and converts it into a specific exit code and a fully translated message.
    """
    msg_lower = raw_message.lower()

    # Case A: Invalid choice or subcommand (e.g., "invalid choice: 'foo' (choose from...)")
    if "invalid choice" in msg_lower:
        match = re.search(r"invalid choice:\s*'([^']+)'", raw_message, re.IGNORECASE)
        cmd_name = match.group(1) if match else raw_message
        return (
            ExitCode.UNKNOWN_COMMAND,
            t("cli_error_cmd_not_found", cmd=cmd_name),
        )

    # Case B: Missing required argument (e.g., "the following arguments are required: -n/--name")
    if "following arguments are required" in msg_lower or "required" in msg_lower:
        match = re.search(r"required:\s*(.+)", raw_message, re.IGNORECASE)
        arg_name = match.group(1).strip() if match else raw_message
        return (
            ExitCode.MISSING_REQUIRED_ARG,
            t("err_missing_required_arg", arg=arg_name),
        )

    # Case C: Unrecognized flag or option (e.g., "unrecognized arguments: --fast")
    if "unrecognized arguments" in msg_lower:
        match = re.search(r"unrecognized arguments:\s*(.+)", raw_message, re.IGNORECASE)
        flag_name = match.group(1).strip() if match else raw_message
        return (
            ExitCode.UNKNOWN_FLAG,
            t("err_unknown_flag", flag=flag_name),
        )

    # Case D: Invalid type or value (e.g., "invalid int value: 'abc'")
    if "invalid" in msg_lower and "value" in msg_lower:
        return (
            ExitCode.INVALID_ARG_TYPE,
            t("err_invalid_arg_type", details=raw_message),
        )

    # Case E: Ambiguity or conflict
    if "ambiguous option" in msg_lower:
        return (
            ExitCode.AMBIGUOUS_ARG,
            t("err_ambiguous_arg", details=raw_message),
        )

    # Fallback: Generic syntax error
    return (
        ExitCode.GENERIC_SYNTAX_ERROR,
        t("err_generic_syntax", details=raw_message),
    )


# ---------------------------------------------------------------------------
# 3. CLI Error Orchestrator / Handler
# ---------------------------------------------------------------------------
def handle_cli_error(
    raw_message: str,
    commands_map: dict,
    invoked_as: str,
    code_override: ExitCode | None = None,
    console: Console | None = None,
    config: Config | None = None
) -> None:
    """
    Intercepts parser/execution errors, renders contextual help
    using cmd_help, and outputs the translated error message to stderr.
    """
    out = console or _default_console

    # 1. Determine exit code and translated message
    if code_override is not None:
        exit_code = code_override
        translated_msg = raw_message
    else:
        exit_code, translated_msg = parse_argparse_error(raw_message)

    # 2. Prepare context to invoke help for the corresponding subcommand
    dummy_args = Namespace()
    setattr(dummy_args, "_commands_map", commands_map)
    setattr(dummy_args, "_invoked_as", invoked_as)

    raw_args = sys.argv[1:]
    detected_subcmd = next((arg for arg in raw_args if arg in commands_map), None)

    if detected_subcmd:
        setattr(dummy_args, "subcommand", detected_subcmd)
        setattr(dummy_args, "_target_cmd", commands_map[detected_subcmd])

    # 3. Print styled help via help.py (passing the custom console out)
    cfg = config or get_config()
    sys_help.run(dummy_args, console=out, config=cfg)

    # 4. Print clean, internationalized error message to stderr
    title = t("cli_error_args_title")
    out.print(f"[bold red]{title}[/bold red] {translated_msg}\n")

    # 5. Exit with the specific assigned code
    sys.exit(int(exit_code))