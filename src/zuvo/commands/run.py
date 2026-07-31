"""
Executes a user CLI application or multicall module in development mode.
"""

import subprocess
import sys
from pathlib import Path

from zuvo.core.config import Config, get_config


# Optional: Override description for i18n key or custom text
HELP = "cmd_run_help"

ARGS = [
    {
        "flags": ["app_target"],
        "type": str,
        "help": "cmd_run_arg_app_target_help"
    },
    {
        "flags": ["extra_args"],
        "nargs": "...",
        "help": "cmd_run_arg_extra_args_help"
    }
]


def run(args, config: Config | None = None,):
    """
    Executes the user's CLI application in development mode.

    Simulates system execution by overriding sys.argv[0] via runpy, ensuring
    full compatibility with standard apps and multicall (busybox-style) modules.
    """
    cfg = config or get_config()
    entry_script = cfg.build.get("entry_point", "src/app/main.py")
    app_target = args.app_target
    extra_args = getattr(args, "extra_args", []) or []

    # If the user passed an explicit .py script path
    if app_target.endswith(".py") and Path(app_target).is_file():
        entry_script = app_target
        simulated_argv0 = cfg.cli_name
    else:
        # app_target is an app name or a multicall context (e.g., 'pepe', 'app1', 'app2')
        simulated_argv0 = app_target

    # Inline Python wrapper overriding sys.argv[0] to simulate execution context
    code_wrapper = (
        "import sys, runpy; "
        f"sys.argv = ['{simulated_argv0}'] + sys.argv[1:]; "
        f"runpy.run_path('{entry_script}', run_name='__main__')"
    )

    cmd = [sys.executable, "-c", code_wrapper] + extra_args

    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        return 130