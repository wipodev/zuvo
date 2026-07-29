import pytest
from rich.console import Console

from zuvo.core.config import Config
from zuvo.core.errors import ExitCode, handle_cli_error, parse_argparse_error


class TestParseArgparseError:
    """Test suite for parsing argparse raw English messages to i18n and ExitCode."""

    def test_parse_invalid_choice(self):
        code, msg = parse_argparse_error("invalid choice: 'run' (choose from 'build', 'version')")
        assert code == ExitCode.UNKNOWN_COMMAND
        # Evalúa contra el texto real traducido: "Command 'run' does not exist or is not callable."
        assert "run" in msg
        assert "does not exist" in msg

    def test_parse_missing_required_arg(self):
        code, msg = parse_argparse_error("the following arguments are required: -n/--name")
        assert code == ExitCode.MISSING_REQUIRED_ARG
        assert "-n/--name" in msg

    def test_parse_unrecognized_arguments(self):
        code, msg = parse_argparse_error("unrecognized arguments: --foo")
        assert code == ExitCode.UNKNOWN_FLAG
        assert "--foo" in msg

    def test_parse_invalid_value(self):
        code, msg = parse_argparse_error("invalid int value: 'abc'")
        assert code == ExitCode.INVALID_ARG_TYPE

    def test_parse_generic_fallback(self):
        code, msg = parse_argparse_error("some unexpected syntax error")
        assert code == ExitCode.GENERIC_SYNTAX_ERROR


class TestHandleCliError:
    """Test suite for CLI error orchestrator."""

    def test_handle_cli_error_exits_with_code(self):
        test_console = Console(record=True, width=100)

        with pytest.raises(SystemExit) as exc_info:
            handle_cli_error(
                raw_message="unrecognized arguments: --bad-flag",
                commands_map={},
                invoked_as="zuvo",
                console=test_console,
                config=Config()
            )

        assert exc_info.value.code == ExitCode.UNKNOWN_FLAG

        output = test_console.export_text()
        assert "--bad-flag" in output

    def test_handle_cli_error_with_override(self):
        test_console = Console(record=True, width=100)

        with pytest.raises(SystemExit) as exc_info:
            handle_cli_error(
                raw_message="Custom error message",
                commands_map={},
                invoked_as="zuvo",
                code_override=ExitCode.COMMAND_EXECUTION_ERROR,
                console=test_console,
                config=Config()
            )

        assert exc_info.value.code == ExitCode.COMMAND_EXECUTION_ERROR

        output = test_console.export_text()
        assert "Custom error message" in output