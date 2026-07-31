import subprocess
from pathlib import Path
from rich.console import Console

_default_console = Console()


def run_system_command(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    console: Console | None = None,
) -> None:
    """
    Executes a system subprocess displaying stderr/stdout lines smoothly.
    Raises RuntimeError if the execution exits with a non-zero code.
    """
    out = console or _default_console
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    if process.stdout:
        for line in process.stdout:
            # Imprime líneas secundarias con formato atenudo para no saturar la consola
            out.print(f"  [dim]›[/dim] {line.strip()}")

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {process.returncode}"
        )