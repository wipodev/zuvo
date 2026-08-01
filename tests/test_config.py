import pytest
from pathlib import Path
from zuvo.core.config import Config, set_config, get_config


class TestConfig:
    """Test suite for configuration loading."""

    def test_default_config_when_file_missing(self, tmp_path: Path):
        """Verify default configuration values when pyproject.toml is missing."""
        config = Config.load(tmp_path)

        assert config.name == "cli-app"
        assert config.version == "0.0.1"

    def test_load_valid_pyproject_toml(self, tmp_path: Path):
        """Verify loading and parsing custom attributes from pyproject.toml."""
        toml_content = """
        [project]
        name = "custom-app"
        version = "2.1.0"
        description = "A custom app"
        authors = [{ name = "Carlos" }]

        [tool.zuvo]
        title = "Custom App Title"
        commands_pkg = "app.commands"
        """
        (tmp_path / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        config = Config.load(tmp_path)

        assert config.name == "custom-app"
        assert config.version == "2.1.0"
        assert config.author == "Carlos"
        assert config.title == "Custom App Title"
        assert config.commands_pkg == "app.commands"

    def test_load_corrupted_pyproject_toml_returns_defaults(self, tmp_path: Path):
        """Verify fallback to default values if pyproject.toml is invalid."""
        (tmp_path / "pyproject.toml").write_text("[invalid toml syntax", encoding="utf-8")

        config = Config.load(tmp_path)

        assert config.name == "cli-app"
        assert config.version == "0.0.1"

    def test_to_dict_serialization(self):
        """Verify serializing a Config instance into a dictionary."""
        config = Config(
            name="dict-app",
            version="1.0.0",
            commands_config={"default": ["build", "run"]},
        )

        dict_data = config.to_dict()

        assert isinstance(dict_data, dict)
        assert dict_data["name"] == "dict-app"
        assert dict_data["version"] == "1.0.0"
        assert dict_data["commands_config"] == {"default": ["build", "run"]}

    def test_from_dict_deserialization(self):
        """Verify reconstructing a Config instance from a dictionary."""
        raw_dict = {
            "name": "restored-app",
            "version": "3.0.0",
            "commands_pkg": "app.commands",
        }

        config = Config.from_dict(raw_dict)

        assert isinstance(config, Config)
        assert config.name == "restored-app"
        assert config.version == "3.0.0"

    def test_global_registry_set_and_get(self):
        """Verify setting and retrieving global config instance."""
        custom_config = Config(name="global-app")
        set_config(custom_config)

        assert get_config() is custom_config
        assert get_config().name == "global-app"

    def test_get_config_raises_runtime_error_when_uninitialized(self, monkeypatch):
        """Verify RuntimeError is raised if get_config is called before set_config."""
        monkeypatch.setattr("zuvo.core.config._instance", None)

        with pytest.raises(RuntimeError, match="Configuration has not been initialized with set_config()."):
            get_config()