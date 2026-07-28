import types
import pytest
from unittest.mock import patch, MagicMock

from zuvo.core.runner import get_invocation_name, load_command_modules, run_app


class TestGetInvocationName:
    """Tests for extracting the executable/invocation name."""

    def test_get_invocation_name_from_argv(self):
        """Verify that it extracts the stem from sys.argv[0] if it is not main or __main__."""
        with patch("sys.argv", ["/usr/bin/my-custom-cli", "arg1"]):
            assert get_invocation_name() == "my-custom-cli"

    def test_get_invocation_name_fallback_to_executable_name(self):
        """Verify that it uses EXECUTABLE_NAME if sys.argv[0] is main or __main__."""
        with patch("sys.argv", ["/app/main.py"]):
            with patch("zuvo.core.runner.EXECUTABLE_NAME", "default_cli"):
                assert get_invocation_name() == "default_cli"

        with patch("sys.argv", ["/app/__main__.py"]):
            with patch("zuvo.core.runner.EXECUTABLE_NAME", "default_cli"):
                assert get_invocation_name() == "default_cli"


class TestLoadCommandModules:
    """Tests for dynamically importing commands (load_command_modules)."""

    def test_load_valid_command_module(self):
        """Verify that it correctly imports modules that implement run(args)."""
        valid_mod = types.ModuleType("src.app.commands.valid_cmd")
        valid_mod.run = lambda args: None  # Implements the required function

        with patch("importlib.import_module", return_value=valid_mod):
            commands = load_command_modules(["valid_cmd"], "src.app.commands")
            assert "valid_cmd" in commands
            assert commands["valid_cmd"] == valid_mod

    def test_load_module_missing_run_warns_stderr(self, capsys, set_language):
        """Verify that it emits a warning to stderr and does NOT register the command if run() is missing."""
        set_language("es")
        broken_mod = types.ModuleType("src.app.commands.broken_cmd")  # Missing run function

        with patch("importlib.import_module", return_value=broken_mod):
            commands = load_command_modules(["broken_cmd"], "src.app.commands")

            captured = capsys.readouterr()
            assert "broken_cmd" not in commands
            assert "Advertencia del Framework" in captured.err or "run(args)" in captured.err

    def test_load_module_not_found(self, capsys, set_language):
        """Verify that it catches ModuleNotFoundError and writes to stderr."""
        set_language("es")

        with patch("importlib.import_module", side_effect=ModuleNotFoundError("No module")):
            commands = load_command_modules(["missing_cmd"], "src.app.commands")

            captured = capsys.readouterr()
            assert "missing_cmd" not in commands
            assert "missing_cmd" in captured.err

    def test_load_module_generic_exception(self, capsys):
        """Verify that it catches any other exception raised when importing a module."""
        with patch("importlib.import_module", side_effect=RuntimeError("Syntax Error inside module")):
            commands = load_command_modules(["corrupt_cmd"], "src.app.commands")

            captured = capsys.readouterr()
            assert "corrupt_cmd" not in commands
            assert "Syntax Error inside module" in captured.err


class TestRunAppOrchestrator:
    """Tests for the main orchestrator run_app()."""

    def test_run_app_standalone_app(self):
        """Verify the normal execution flow when APP_TYPE is not 'module'."""
        with patch("zuvo.core.runner.APP_TYPE", "standalone"), \
             patch("zuvo.core.runner.COMMANDS_CONFIG", ["create", "install"]), \
             patch("zuvo.core.runner.get_invocation_name", return_value="mycli"), \
             patch("zuvo.core.runner.load_command_modules", return_value={"create": MagicMock()}) as mock_load, \
             patch("zuvo.core.runner.build_parser_and_run") as mock_build_run:

            run_app()

            # Corregido a la ruta estándar de la plantilla: "src.app.commands"
            mock_load.assert_called_once_with(["create", "install"], "src.app.commands")
            mock_build_run.assert_called_once()

    def test_run_app_module_app_recognized_context(self):
        """Verify the flow when APP_TYPE == 'module' and the executable matches a valid key."""
        commands_config = {"app1": ["init", "build"]}

        with patch("zuvo.core.runner.APP_TYPE", "module"), \
             patch("zuvo.core.runner.COMMANDS_CONFIG", commands_config), \
             patch("zuvo.core.runner.get_invocation_name", return_value="app1"), \
             patch("zuvo.core.runner.load_command_modules", return_value={"init": MagicMock()}) as mock_load, \
             patch("zuvo.core.runner.build_parser_and_run") as mock_build_run:

            run_app()

            # Corregido a la ruta contextual de la plantilla: "src.app.commands.app1"
            mock_load.assert_called_once_with(["init", "build"], "src.app.commands.app1")
            mock_build_run.assert_called_once()

    def test_run_app_module_app_unrecognized_context(self, capsys):
        """Verify that if APP_TYPE == 'module' but context is unrecognized, it exits with sys.exit(1)."""
        commands_config = {"app1": ["init"]}

        with patch("zuvo.core.runner.APP_TYPE", "module"), \
             patch("zuvo.core.runner.COMMANDS_CONFIG", commands_config), \
             patch("zuvo.core.runner.get_invocation_name", return_value="unknown_context"):

            with pytest.raises(SystemExit) as exc_info:
                run_app()

            captured = capsys.readouterr()
            assert exc_info.value.code == 1
            assert "unknown_context" in captured.err