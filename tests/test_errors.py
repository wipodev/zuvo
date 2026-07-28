import pytest
from unittest.mock import patch, MagicMock
from zuvo.core.errors import (
    ExitCode,
    parse_argparse_error,
    handle_cli_error,
)


class TestParseArgparseError:
    """Unit test suite for the argparse message parser."""

    def test_invalid_choice_unknown_command(self, set_language):
        """Case A: Unrecognized subcommand."""
        set_language("es")
        raw = "invalid choice: 'foo' (choose from create, install)"
        
        code, msg = parse_argparse_error(raw)
        
        assert code == ExitCode.UNKNOWN_COMMAND
        assert "foo" in msg

    def test_missing_required_argument(self, set_language):
        """Case B: Missing required argument."""
        set_language("es")
        raw = "the following arguments are required: -n/--name"
        
        code, msg = parse_argparse_error(raw)
        
        assert code == ExitCode.MISSING_REQUIRED_ARG
        assert "-n/--name" in msg

    def test_unrecognized_arguments_flag(self, set_language):
        """Case C: Unrecognized flag."""
        set_language("es")
        raw = "unrecognized arguments: --flag-inexistente"
        
        code, msg = parse_argparse_error(raw)
        
        assert code == ExitCode.UNKNOWN_FLAG
        assert "--flag-inexistente" in msg

    def test_invalid_type_value(self, set_language):
        """Case D: Invalid type value (e.g., text provided where a number was expected)."""
        set_language("es")
        raw = "invalid int value: 'abc'"
        
        code, msg = parse_argparse_error(raw)
        
        assert code == ExitCode.INVALID_ARG_TYPE
        assert raw in msg

    def test_ambiguous_option(self, set_language):
        """Case E: Ambiguous or confusing option."""
        set_language("es")
        raw = "ambiguous option: --p could match --port, --path"
        
        code, msg = parse_argparse_error(raw)
        
        assert code == ExitCode.AMBIGUOUS_ARG
        assert raw in msg

    def test_fallback_generic_syntax_error(self, set_language):
        """Fallback Case: Any error message not handled by the Regex patterns."""
        set_language("es")
        raw = "Custom unexpected syntax exception details"
        
        code, msg = parse_argparse_error(raw)
        
        assert code == ExitCode.GENERIC_SYNTAX_ERROR
        assert raw in msg


class TestHandleCliError:
    """Test suite for the orchestrator and main CLI error handler."""

    def test_handle_cli_error_normal_flow(self, capsys, set_language):
        """
        Verify that handle_cli_error executes help output, prints the error to stderr,
        and terminates the process with sys.exit() using the appropriate exit code.
        """
        set_language("es")
        commands_map = {"create": MagicMock()}

        with patch("sys.argv", ["cli_template", "create"]), \
             patch("zuvo.system_cmds.help.run") as mock_help_run:
            
            with pytest.raises(SystemExit) as exc_info:
                handle_cli_error(
                    raw_message="the following arguments are required: --name",
                    commands_map=commands_map,
                    invoked_as="cli_template"
                )

            # 1. Should have called the help function
            assert mock_help_run.called

            # 2. Should exit with the code corresponding to missing required argument
            assert exc_info.value.code == ExitCode.MISSING_REQUIRED_ARG

            # 3. Error output in stderr should contain the translated title and detail
            captured = capsys.readouterr()
            assert "Error de Argumento:" in captured.err or "obligatorio" in captured.err
            assert "--name" in captured.err

    def test_handle_cli_error_code_override(self, capsys):
        """
        Verify that if code_override is provided, it skips Regex parsing and directly uses
        the provided exit code and message.
        """
        commands_map = {}
        override_code = ExitCode.INVALID_COMMAND_MODULE
        override_msg = "Mensaje directo sin pasar por parse_argparse_error"

        with patch("sys.argv", ["cli_template"]), \
             patch("zuvo.system_cmds.help.run"):
            
            with pytest.raises(SystemExit) as exc_info:
                handle_cli_error(
                    raw_message=override_msg,
                    commands_map=commands_map,
                    invoked_as="cli_template",
                    code_override=override_code
                )

            # Explicitly overridden exit code
            assert exc_info.value.code == override_code

            # Raw message should appear directly in stderr
            captured = capsys.readouterr()
            assert override_msg in captured.err