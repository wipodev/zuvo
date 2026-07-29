from types import SimpleNamespace
from rich.console import Console

from zuvo.system_cmds.help import run, _get_clean_doc
from zuvo.core import config


class DummySubCommand:
    """A dummy subcommand for testing help rendering."""

    HELP = "A test subcommand help"
    ARGS = [
        {"flags": ["-f", "--file"], "help": "Path to file", "required": True},
        {"flags": ["--verbose"], "action": "store_true", "help": "Enable verbose mode"},
    ]


class TestHelpCommand:
    """Test suite for the help command."""

    def test_get_clean_doc_from_help_attr(self):
        """Verify that _get_clean_doc reads from HELP attribute first."""
        doc = _get_clean_doc(DummySubCommand)
        assert doc == "A test subcommand help"

    def test_show_general_help(self, monkeypatch):
        """Verify that run() renders general help menu when no target_cmd is specified."""
        monkeypatch.setattr(config, "TITLE", "Zuvo Test")
        monkeypatch.setattr(config, "VERSION", "1.0.0")

        test_console = Console(record=True, width=100)
        args = SimpleNamespace(
            _commands_map={"test_cmd": DummySubCommand},
            _invoked_as="zuvo",
            _target_cmd=None,
        )

        run(args=args, console=test_console)

        output = test_console.export_text()

        assert "Zuvo Test" in output
        assert "v1.0.0" in output
        assert "test_cmd" in output
        assert "-h, --help" in output

    def test_show_subcommand_help(self):
        """Verify that run() renders detailed subcommand help when _target_cmd is present."""
        test_console = Console(record=True, width=100)
        args = SimpleNamespace(
            _commands_map={},
            _invoked_as="zuvo",
            _target_cmd=DummySubCommand,
            subcommand="my_subcmd",
        )

        run(args=args, console=test_console)

        output = test_console.export_text()

        assert "my_subcmd" in output
        assert "-f, --file" in output
        assert "--verbose" in output