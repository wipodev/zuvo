import pytest
from pathlib import Path
from zuvo.core.config import Config, _to_pkg_path


class TestConfig:
    """Test suite for configuration loading."""

    def test_to_pkg_path_conversion(self):
        """Verify converting filesystem paths to Python package paths."""
        assert _to_pkg_path("src/app/commands") == "src.app.commands"
        assert _to_pkg_path("src\\app\\commands") == "src.app.commands"

    def test_default_config_when_file_missing(self, tmp_path: Path):
        """Verify default configuration values when pyproject.toml is missing."""
        config = Config.load(tmp_path)

        assert config.name == "cli-app"
        assert config.version == "0.0.1"
        assert config.locales_dir == tmp_path / "locales"

    def test_load_valid_pyproject_toml(self, tmp_path: Path):
        """Verify loading and parsing custom attributes from pyproject.toml."""
        toml_content = """
        [project]
        name = "custom-app"
        version = "2.1.0"
        description = "A custom app"
        authors = [{ name = "Carlos" }]

        [tool.zuvo]
        type = "advanced"
        title = "Custom App Title"
        commands_dir = "src/custom/commands"
        locales_dir = "my_locales"
        """
        (tmp_path / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        config = Config.load(tmp_path)

        assert config.name == "custom-app"
        assert config.version == "2.1.0"
        assert config.author == "Carlos"
        assert config.app_type == "advanced"
        assert config.title == "Custom App Title"
        assert config.commands_pkg == "src.custom.commands"
        assert config.locales_dir == tmp_path / "my_locales"

    def test_load_corrupted_pyproject_toml_returns_defaults(self, tmp_path: Path):
        """Verify fallback to default values if pyproject.toml is invalid."""
        (tmp_path / "pyproject.toml").write_text("[invalid toml syntax", encoding="utf-8")

        config = Config.load(tmp_path)

        assert config.name == "cli-app"
        assert config.version == "0.0.1"