import types
from unittest.mock import patch
from zuvo.core.runner import load_command_modules
from zuvo.core.errors import ExitCode


class TestCLIErrors:
    """Test suite for validating exit codes and error message translations."""

    def test_missing_required_arg(self, cli_runner, set_language):
        """Verify that omitting a required argument returns ExitCode.MISSING_REQUIRED_ARG (10)."""
        set_language("es")
        exit_code, stdout, stderr = cli_runner(["create"])

        assert exit_code == ExitCode.MISSING_REQUIRED_ARG
        assert "Error de Argumentos:" in stderr
        assert "requerido" in stderr or "--name" in stderr

    def test_unknown_flag(self, cli_runner, set_language):
        """Verify that using a non-existent flag returns ExitCode.UNKNOWN_FLAG (11)."""
        set_language("es")
        exit_code, stdout, stderr = cli_runner(["create", "-n", "Demo", "--flag-inventado"])

        assert exit_code == ExitCode.UNKNOWN_FLAG
        assert "Opción o flag no reconocida" in stderr or "--flag-inventado" in stderr

    def test_unknown_command(self, cli_runner, set_language):
        """Verify that a non-existent subcommand returns ExitCode.UNKNOWN_COMMAND (2)."""
        set_language("es")
        exit_code, stdout, stderr = cli_runner(["comando_inexistente"])

        assert exit_code == ExitCode.UNKNOWN_COMMAND
        assert "no existe" in stderr or "comando_inexistente" in stderr

    def test_success_command(self, cli_runner):
        """Verify that a valid command returns ExitCode.SUCCESS (0)."""
        exit_code, stdout, stderr = cli_runner(["create", "-n", "MiRecurso"])

        assert exit_code == ExitCode.SUCCESS
        assert "Resource Name" in stdout or "MiRecurso" in stdout

    def test_i18n_fallback_english(self, cli_runner, set_language):
        """Verify dynamic translation when changing the language to English."""
        set_language("en")
        exit_code, stdout, stderr = cli_runner(["create"])

        assert exit_code == ExitCode.MISSING_REQUIRED_ARG
        assert "Argument Error:" in stderr
        assert "The following argument is required:" in stderr

    def test_load_command_modules_warns_missing_run(self, capsys, set_language):
        """
        Verify that load_command_modules prints an explanatory warning to stderr
        and skips registering the command when a module is missing the run() function.
        """
        set_language("es")

        # Create a mock module without the run() function
        broken_module = types.ModuleType("zuvo.template.src.app.commands.broken_cmd")
        broken_module.ARGS = []

        # Patch importlib to intercept loading 'zuvo.template.src.app.commands.broken_cmd'
        with patch("importlib.import_module", return_value=broken_module):
            commands = load_command_modules(["broken_cmd"], "zuvo.template.src.app.commands")

            captured = capsys.readouterr()

            # 1. The command must NOT be registered in the returned dictionary
            assert "broken_cmd" not in commands

            # 2. Must emit the educational warning to stderr
            assert "Advertencia del Framework" in captured.err
            assert "run(args)" in captured.err
            assert "broken_cmd" in captured.err

    def test_global_version_flag(self, cli_runner):
        """Verify that --version responds correctly with ExitCode.SUCCESS (0)."""
        exit_code, stdout, stderr = cli_runner(["--version"])

        assert exit_code == ExitCode.SUCCESS
        assert stdout != "" or stderr != ""  # Should print the version to either stdout or stderr

    def test_global_help_flag(self, cli_runner):
        """Verify that invoking with no arguments or -h / --help displays general help."""
        exit_code, stdout, stderr = cli_runner(["--help"])

        assert exit_code == ExitCode.SUCCESS
        assert "Uso:" in stdout or "Usage:" in stdout or "help" in stdout.lower()

    def test_subcommand_help_flag(self, cli_runner):
        """Verify that asking for help on a subcommand (e.g., create -h) displays its help and returns 0."""
        exit_code, stdout, stderr = cli_runner(["create", "--help"])

        assert exit_code == ExitCode.SUCCESS
        assert "create" in stdout or "create" in stderr

    def test_subcommand_runtime_exception(self, cli_runner):
        """Verify that an unhandled error in a command returns ExitCode.COMMAND_EXECUTION_ERROR."""
        # Force a command's 'run' function to raise an unhandled exception
        with patch("zuvo.template.src.app.commands.create.run", side_effect=RuntimeError("Error de base de datos")):
            exit_code, stdout, stderr = cli_runner(["create", "-n", "TestApp"])

            assert exit_code == ExitCode.COMMAND_EXECUTION_ERROR
            assert "Error de base de datos" in stderr