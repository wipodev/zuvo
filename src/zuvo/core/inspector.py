"""
Core command introspection and metadata extraction engine.
"""

from dataclasses import dataclass
from typing import Any

from zuvo.i18n import t
from zuvo.utils.paths import resolve_command_module


def extract_clean_doc(cmd_module: Any) -> str:
    """
    Extracts a clean command description from HELP, docstrings, or fallback value.

    Args:
        cmd_module: The command module instance to inspect.

    Returns:
        str: Resolved description string.
    """
    help_attr = getattr(cmd_module, "HELP", None)
    if help_attr:
        return t(str(help_attr).strip())

    doc = None
    if hasattr(cmd_module, "run"):
        doc = getattr(cmd_module.run, "__doc__", None)
    if not doc:
        doc = getattr(cmd_module, "__doc__", None)

    if not doc:
        return t("help_no_description")

    return str(doc).strip()


@dataclass
class ArgumentDoc:
    """
    Data container for command argument documentation.
    """

    flags: list[str]
    description: str
    default: Any
    choices: list[Any] | None
    required: bool


@dataclass
class CommandDoc:
    """
    Data container for single command metadata.
    """

    name: str
    description: str
    file_path: str
    arguments: list[ArgumentDoc]
    raw_module: Any = None


@dataclass
class AppDoc:
    """
    Data container for application level commands documentation.
    """

    app_name: str
    commands: list[CommandDoc]


def extract_command_doc(
    cmd_name: str,
    mod: Any,
    base_pkg: str = "",
    app_name: str = "",
) -> CommandDoc:
    """
    Extracts structured documentation metadata from a command module.

    Args:
        cmd_name: Name of the command.
        mod: The command module instance.
        base_pkg: Base package string for file path resolution.
        app_name: Application name context.

    Returns:
        CommandDoc: Normalized command metadata.
    """
    description = extract_clean_doc(mod)

    rel_file = ""
    if base_pkg:
        module_path, _ = resolve_command_module(base_pkg, app_name, cmd_name)
        rel_file = module_path.replace(".", "/") + ".py"

    raw_args = getattr(mod, "ARGS", [])
    parsed_args: list[ArgumentDoc] = []

    for arg in raw_args:
        flags = arg.get("flags", [])
        arg_help_key = arg.get("help", "")
        arg_desc = t(arg_help_key) if arg_help_key else ""
        default_val = arg.get("default", None)
        choices = arg.get("choices", None)
        required = bool(arg.get("required", False))

        parsed_args.append(
            ArgumentDoc(
                flags=flags,
                description=arg_desc,
                default=default_val,
                choices=choices,
                required=required,
            )
        )

    return CommandDoc(
        name=cmd_name,
        description=description,
        file_path=rel_file,
        arguments=parsed_args,
        raw_module=mod,
    )