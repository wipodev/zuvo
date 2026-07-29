import pytest
from rich.console import Console

from zuvo.core.errors import ExitCode
from zuvo.core.runner import build_parser_and_run


class DummyValidCommand:
    """A valid subcommand implementation."""

    HELP = "Demo command"
    ARGS = [{"flags": ["-n", "--name"], "help": "Name arg"}]

    executed = False

    @classmethod
    def run(cls, args):
        cls.executed = True


class DummyInvalidCommand:
    """An invalid subcommand missing the run method."""

    NAME = "broken"


class TestRunnerLifecycle:
    """Test suite for CLI runner lifecycle orchestrator."""

    def test_run_version_flag_exits_success(self):
        """Verify -v exits with SUCCESS code."""
        test_console = Console(record=True, width=100)

        with pytest.raises(SystemExit) as exc_info:
            build_parser_and_run(
                commands_map={"demo": DummyValidCommand},
                invoked_as="zuvo",
                argv=["-v"],
                console=test_console,
            )

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_run_help_flag_exits_success(self):
        """Verify -h exits with SUCCESS code."""
        test_console = Console(record=True, width=100)

        with pytest.raises(SystemExit) as exc_info:
            build_parser_and_run(
                commands_map={"demo": DummyValidCommand},
                invoked_as="zuvo",
                argv=["--help"],
                console=test_console,
            )

        assert exc_info.value.code == ExitCode.SUCCESS

    def test_dispatch_valid_command(self):
        """Verify valid command is dispatched and executed properly."""
        DummyValidCommand.executed = False

        build_parser_and_run(
            commands_map={"demo": DummyValidCommand},
            invoked_as="zuvo",
            argv=["demo", "--name", "Test"],
        )

        assert DummyValidCommand.executed is True

    def test_dispatch_invalid_command_module_exits(self):
        """Verify calling a command module without run() raises INVALID_COMMAND_MODULE."""
        test_console = Console(record=True, width=100)

        with pytest.raises(SystemExit) as exc_info:
            build_parser_and_run(
                commands_map={"broken": DummyInvalidCommand},
                invoked_as="zuvo",
                argv=["broken"],
                console=test_console,
            )

        assert exc_info.value.code == ExitCode.INVALID_COMMAND_MODULE