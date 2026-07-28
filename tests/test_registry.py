import argparse
import sys
from unittest.mock import MagicMock, patch

import pytest

from zuvo.core.errors import ExitCode
from zuvo.core.registry import (
    _build_parser,
    _dispatch_command,
    _handle_global_flags,
    _register_command_args,
    build_parser_and_run,
)


class TestRegistryCore:
    """Unit tests for internal functions and lifecycle in registry.py."""

    # -------------------------------------------------------------------
    # Tests for _register_command_args
    # -------------------------------------------------------------------
    def test_register_command_args_standard(self):
        """Verify that arguments declared in ARGS are registered correctly."""
        parser = argparse.ArgumentParser()
        args_def = [
            {"flags": ["-n", "--name"], "type": str, "required": True},
            {"flags": ["--count"], "type": int, "default": 1},
        ]

        with patch.object(sys, "argv", ["mycli", "test"]):
            _register_command_args(parser, args_def)

        parsed = parser.parse_args(["-n", "wipo", "--count", "5"])
        assert parsed.name == "wipo"
        assert parsed.count == 5

    def test_register_command_args_bypasses_required_on_help(self):
        """Verify that requesting help (-h) prevents required argument errors in the parser."""
        parser = argparse.ArgumentParser()
        args_def = [{"flags": ["-r", "--req"], "type": str, "required": True}]

        # Simulate user passing --help in sys.argv
        with patch.object(sys, "argv", ["mycli", "cmd", "--help"]):
            _register_command_args(parser, args_def)

            # Find the registered action in the parser
            action = next(a for a in parser._actions if "--req" in a.option_strings)
            assert action.required is False

    # -------------------------------------------------------------------
    # Tests for _build_parser
    # -------------------------------------------------------------------
    def test_build_parser_structure(self):
        """Verify basic parser construction and subcommand registration."""
        dummy_cmd = MagicMock()
        dummy_cmd.ARGS = [{"flags": ["--foo"], "type": str}]
        commands_map = {"dummy": dummy_cmd}

        parser = _build_parser(commands_map, invoked_as="test-cli")

        # Test parsing global -v flag
        args = parser.parse_args(["-v"])
        assert args.version is True

        # Test parsing subcommand with its argument
        args_sub = parser.parse_args(["dummy", "--foo", "bar"])
        assert args_sub.subcommand == "dummy"
        assert args_sub.foo == "bar"

    # -------------------------------------------------------------------
    # Tests for _handle_global_flags
    # -------------------------------------------------------------------
    @patch("zuvo.core.registry.sys_version.run")
    def test_handle_global_flags_version(self, mock_version_run):
        """Verify interception of version flag or subcommand."""
        args = argparse.Namespace(version=True, subcommand=None, help=False)

        with pytest.raises(SystemExit) as exc_info:
            _handle_global_flags(args)

        assert exc_info.value.code == int(ExitCode.SUCCESS)
        mock_version_run.assert_called_once_with(args)

    @patch("zuvo.core.registry.sys_help.run")
    def test_handle_global_flags_help(self, mock_help_run):
        """Verify help interception when no subcommand is given or help is explicitly requested."""
        args = argparse.Namespace(version=False, subcommand=None, help=True)

        with pytest.raises(SystemExit) as exc_info:
            _handle_global_flags(args)

        assert exc_info.value.code == int(ExitCode.SUCCESS)
        mock_help_run.assert_called_once_with(args)

    # -------------------------------------------------------------------
    # Tests for _dispatch_command
    # -------------------------------------------------------------------
    def test_dispatch_command_success(self):
        """Verify successful execution of the selected subcommand's run function."""
        mock_cmd = MagicMock()
        commands_map = {"run_me": mock_cmd}
        args = argparse.Namespace(subcommand="run_me", help=False)

        _dispatch_command(args, commands_map)
        mock_cmd.run.assert_called_once_with(args)

    @patch("zuvo.core.registry.handle_cli_error")
    def test_dispatch_command_missing_run_fn(self, mock_handle_error):
        """Verify error handling when the command module does not implement 'run'."""
        # Simulate handle_cli_error stopping CLI execution
        mock_handle_error.side_effect = SystemExit(int(ExitCode.INVALID_COMMAND_MODULE))

        invalid_cmd = object()  # Object without run method
        commands_map = {"broken": invalid_cmd}
        args = argparse.Namespace(subcommand="broken", help=False, _invoked_as="app")

        with pytest.raises(SystemExit) as exc_info:
            _dispatch_command(args, commands_map)

        assert exc_info.value.code == int(ExitCode.INVALID_COMMAND_MODULE)
        mock_handle_error.assert_called_once()
        assert mock_handle_error.call_args.kwargs["code_override"] == ExitCode.INVALID_COMMAND_MODULE

    @patch("zuvo.core.registry.sys_help.run")
    def test_dispatch_command_explicit_subcommand_help(self, mock_help_run):
        """Verify interception when requesting help for a subcommand (e.g., app cmd -h)."""
        mock_cmd = MagicMock()
        commands_map = {"mycmd": mock_cmd}
        args = argparse.Namespace(subcommand="mycmd", help=True)

        with pytest.raises(SystemExit) as exc_info:
            _dispatch_command(args, commands_map)

        assert exc_info.value.code == int(ExitCode.SUCCESS)
        assert getattr(args, "_target_cmd") == mock_cmd
        mock_help_run.assert_called_once_with(args)

    def test_dispatch_command_execution_exception(self):
        """Verify handling when subcommand execution raises an exception."""
        failing_cmd = MagicMock()
        failing_cmd.run.side_effect = Exception("Unexpected crash")
        commands_map = {"fail": failing_cmd}
        args = argparse.Namespace(subcommand="fail", help=False)

        with pytest.raises(SystemExit) as exc_info:
            _dispatch_command(args, commands_map)

        assert exc_info.value.code == int(ExitCode.COMMAND_EXECUTION_ERROR)

    # -------------------------------------------------------------------
    # Orchestrator Integration Test: build_parser_and_run
    # -------------------------------------------------------------------
    @patch("zuvo.core.registry._dispatch_command")
    @patch("zuvo.core.registry._handle_global_flags")
    def test_build_parser_and_run_flow(self, mock_handle_flags, mock_dispatch):
        """Verify complete integration flow for the build_parser_and_run orchestrator."""
        mock_cmd = MagicMock()
        commands_map = {"status": mock_cmd}
        mock_handle_flags.return_value = False

        test_args = ["my-cli", "status"]
        with patch.object(sys, "argv", test_args):
            build_parser_and_run(commands_map, invoked_as="my-cli")

        mock_handle_flags.assert_called_once()
        mock_dispatch.assert_called_once()