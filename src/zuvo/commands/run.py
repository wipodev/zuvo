import sys
import subprocess
from pathlib import Path
from typing import List
import tomllib  # O import tomli para Python < 3.11

HELP = "Executes the current project or a configured script."

ARGS = [
    {
        "flags": ["target_and_args"],
        "nargs": "*",
        "help": "Script name or executable target followed by subcommand arguments."
    }
]

def run(args):
    cwd = Path.cwd()
    toml_path = cwd / "pyproject.toml"

    if not toml_path.exists():
        print("[red]Error:[/red] No pyproject.toml found in current directory.")
        return 1

    # 1. Cargar el pyproject.toml del target
    with open(toml_path, "rb") as f:
        config = tomllib.load(f)

    zuvo_config = config.get("tool", {}).get("zuvo", {})
    scripts = zuvo_config.get("scripts", {})
    executable_name = zuvo_config.get("executable_name", "app")
    main_entry = zuvo_config.get("main", "src/main.py")

    raw_args: List[str] = getattr(args, "target_and_args", [])
    
    if not raw_args:
        print(f"[yellow]Usage:[/yellow] zuvo run <{executable_name}|script_name> [args...]")
        return 1

    target = raw_args[0]
    extra_args = raw_args[1:]

    # 2. Caso A: Es un script corto (ej: zuvo run test1)
    if target in scripts:
        full_command_str = scripts[target]
        # Devuelve ej: "python src/app/main.py install --dev"
        cmd_list = [sys.executable] + full_command_str.split()
        return subprocess.run(cmd_list, cwd=cwd).returncode

    # 3. Caso B: Es el nombre de la app (ej: zuvo run miapp install --dev)
    if target == executable_name or target == "app":
        # Ejecuta directamente el main.py del proyecto pasando los subcomandos
        cmd_list = [sys.executable, str(cwd / main_entry)] + extra_args
        return subprocess.run(cmd_list, cwd=cwd).returncode

    print(f"[red]Error:[/red] Unknown script or target '{target}'.")
    return 1