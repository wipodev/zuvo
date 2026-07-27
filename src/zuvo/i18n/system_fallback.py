"""
Global fallback translations for the CLI core template.
Guarantees base UI rendering in English if external JSON files are missing or corrupted.
"""

SYSTEM_FALLBACK: dict[str, str] = {
    # examples Commands
    "cmd_install_help": "Installs all necessary environment dependencies.",
    "cmd_install_arg_dev_help": "Include development dependencies",
    "cmd_create_help": "Creates a new resource within the project workspace.",
    "cmd_create_arg_name_help": "Target name of the new resource.",
    "cmd_create_arg_force_help": "Force overwrite if the target resource already exists.",
}