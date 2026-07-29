from rich.console import Console
from zuvo.system_cmds.version import run
from zuvo.core import config


class TestVersionCommand:
    """Test suite for the version CLI command."""

    def test_run_command_outputs_metadata(self, monkeypatch):
        """Verify that run() renders the project metadata correctly on the console."""
        # Simular metadatos en config
        monkeypatch.setattr(config, "TITLE", "Zuvo Test")
        monkeypatch.setattr(config, "VERSION", "1.2.3")
        monkeypatch.setattr(config, "NAME", "zuvo-test")
        monkeypatch.setattr(config, "EXECUTABLE_NAME", "zuvo_cli")
        monkeypatch.setattr(config, "DESCRIPTION", "Test description")
        monkeypatch.setattr(config, "AUTHOR", "Developer")
        monkeypatch.setattr(config, "COPYRIGHT", "2026 Zuvo")

        # Usar una consola en memoria para capturar la salida de Rich
        test_console = Console(record=True, width=100)
        
        run(console=test_console)
        
        output = test_console.export_text()

        # Aserciones sobre la salida formateada
        assert "Zuvo Test" in output
        assert "v1.2.3" in output
        assert "zuvo-test" in output
        assert "zuvo_cli" in output
        assert "Test description" in output
        assert "Developer" in output
        assert "2026 Zuvo" in output