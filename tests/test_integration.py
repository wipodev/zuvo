import os
from pathlib import Path
import subprocess
import sys

from zuvo.core.errors import ExitCode

BLUEPRINT_DIR = Path(__file__).parent / "blueprint_project"
MAIN_SCRIPT = BLUEPRINT_DIR / "src" / "app" / "main.py"


def run_cli_submodule(args: list[str], lang: str = "en") -> subprocess.CompletedProcess:
    """
    Executes the main.py entrypoint script as a subprocess inside the blueprint directory.

    Args:
        args (list[str]): List of CLI arguments to pass to main.py.
        lang (str): Language code for internationalization testing.

    Returns:
        subprocess.CompletedProcess: Process output including stdout, stderr, and returncode.
    """
    env = os.environ.copy()
    env["LANG"] = f"{lang}.UTF-8"
    env["LANGUAGE"] = lang
    env["PYTHONPATH"] = str(Path.cwd())
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    return subprocess.run(
        [sys.executable, str(MAIN_SCRIPT)] + args,
        cwd=BLUEPRINT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


class TestBlueprintE2E:
    """End-to-End integration tests invoking main.py directly via subprocess."""

    def test_global_help_output(self):
        """Tests 'python src/app/main.py -h' output and exit code."""
        result = run_cli_submodule(["-h"])

        assert result.returncode == ExitCode.SUCCESS
        output = result.stdout + result.stderr
        assert "cli_test" in output

    def test_global_version_output(self):
        """Tests 'python src/app/main.py -v' output and exit code."""
        result = run_cli_submodule(["-v"])

        assert result.returncode == ExitCode.SUCCESS
        output = result.stdout + result.stderr
        assert "0.1.0" in output

    def test_subcommand_help_output(self):
        """Tests 'python src/app/main.py create -h' output."""
        result = run_cli_submodule(["create", "-h"])

        assert result.returncode == ExitCode.SUCCESS
        output = result.stdout + result.stderr
        assert "create" in output

    def test_create_command_valid_invocation(self):
        """Tests 'python src/app/main.py create -n nombre' with valid arguments."""
        result = run_cli_submodule(["create", "-n", "nombre"])

        assert result.returncode == ExitCode.SUCCESS
        output = result.stdout + result.stderr
        assert "nombre" in output

    def test_create_command_with_optional_flags(self):
        """Tests 'python src/app/main.py create -n nombre --force'."""
        result = run_cli_submodule(["create", "-n", "nombre", "--force"])

        assert result.returncode == ExitCode.SUCCESS
        output = result.stdout + result.stderr
        assert "nombre" in output
        assert "True" in output

    def test_create_command_missing_required_arg(self):
        """Tests 'python src/app/main.py create' when required -n/--name flag is omitted."""
        result = run_cli_submodule(["create"])

        assert result.returncode == ExitCode.MISSING_REQUIRED_ARG

    def test_unknown_command_handling(self):
        """Tests 'python src/app/main.py invalid_cmd' for proper exit code."""
        result = run_cli_submodule(["invalid_cmd"])

        assert result.returncode == ExitCode.UNKNOWN_COMMAND
        output = result.stdout + result.stderr
        assert "invalid_cmd" in output

    def test_create_command_invalid_flag(self):
        """Tests 'python src/app/main.py create -p' when providing an unrecognized flag."""
        result = run_cli_submodule(["create", "-p"])

        assert result.returncode == ExitCode.UNKNOWN_FLAG
        output = result.stdout + result.stderr
        assert "-p" in output

    def test_spanish_localization(self):
        """Tests execution output localized in Spanish via system environment."""
        result = run_cli_submodule(["-h"], lang="es")

        assert result.returncode == ExitCode.SUCCESS
        output = result.stdout + result.stderr
        assert "Uso:" in output or "Comandos" in output or "Opciones" in output