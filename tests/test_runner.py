import pytest
from rich.console import Console

from zuvo.core.config import Config
from zuvo.core.errors import ExitCode
from zuvo.core.runner import get_invocation_name, load_command_modules, run_app


class TestRunnerBootstrapper:
    """Test suite for CLI application bootstrapper (runner.py)."""

    def test_get_invocation_name_default(self):
        assert get_invocation_name("/usr/bin/zuvo") == "zuvo"
        assert get_invocation_name("C:\\app\\zuvo.exe") == "zuvo"

    def test_get_invocation_name_main_fallback(self):
        # When called as 'python -m module' or 'python main.py', falls back to EXECUTABLE_NAME
        assert get_invocation_name("/path/to/__main__.py") != "__main__"
        assert get_invocation_name("/path/to/main.py") != "main"

    def test_load_command_modules_warns_on_missing(self):
        test_console = Console(record=True, width=100)

        commands = load_command_modules(
            command_names=["non_existent_cmd_xyz"],
            package_path="zuvo.commands",
            console=test_console,
        )

        assert "non_existent_cmd_xyz" not in commands
        output = test_console.export_text()
        assert "non_existent_cmd_xyz" in output

    def test_run_app_invalid_module_context_exits(self, monkeypatch):
        test_console = Console(record=True, width=100)

        mock_config = Config(
            app_type="module",
            commands_config={"valid_ctx": []},
        )

        with pytest.raises(SystemExit) as exc_info:
            run_app(argv=["--help"], console=test_console, config=mock_config)

        assert exc_info.value.code == ExitCode.UNKNOWN_CONTEXT