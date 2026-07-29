from rich.console import Console
from zuvo.system_cmds.version import run
from zuvo.core.config import Config


class TestVersionCommand:
    """Test suite for the version CLI command."""

    def test_run_command_outputs_metadata(self):
        """Verify that run() renders the project metadata correctly on the console."""
        mock_config = Config(
            title="Zuvo Test",
            version="1.2.3",
            name="zuvo-test",
            executable_name="zuvo_cli",
            description="Test description",
            author="Developer",
            copyright="2026 Zuvo",
        )

        # Usar una consola en memoria para capturar la salida de Rich
        test_console = Console(record=True, width=100)
        
        run(console=test_console, config=mock_config)
        
        output = test_console.export_text()

        # Aserciones sobre la salida formateada
        assert "Zuvo Test" in output
        assert "v1.2.3" in output
        assert "zuvo-test" in output
        assert "zuvo_cli" in output
        assert "Test description" in output
        assert "Developer" in output
        assert "2026 Zuvo" in output