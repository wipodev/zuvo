import importlib
from unittest.mock import patch

import zuvo.core.project


class TestProjectConfig:
    """Test suite for reading and initializing project configuration."""

    def test_project_default_fallback_values(self):
        """Verify that default values are loaded if read_json_safe returns None."""
        with patch("zuvo.utils.fs_utils.read_json_safe", return_value=None):
            importlib.reload(zuvo.core.project)

            assert zuvo.core.project.NAME == "cli-app"
            assert zuvo.core.project.EXECUTABLE_NAME == "cli-app"
            assert zuvo.core.project.TITLE == "cli-app"
            assert zuvo.core.project.VERSION == "0.0.1"
            assert zuvo.core.project.DESCRIPTION == ""
            assert zuvo.core.project.AUTHOR == ""
            assert zuvo.core.project.COPYRIGHT == ""
            assert zuvo.core.project.APP_TYPE == "standard"
            assert zuvo.core.project.MODULES == []
            assert zuvo.core.project.COMMANDS_CONFIG == []
            assert zuvo.core.project.FILES == []

    def test_project_custom_config_standard_type(self):
        """Verify correct metadata loading from a standard configuration."""
        project_data = {
            "name": "my-tool",
            "executable_name": "tool-cli",
            "title": "My Custom Tool",
            "version": "1.5.0",
            "description": "Una herramienta increíble",
            "author": "Wipo",
            "copyright": "2026 Wipo",
            "type": "standard",
            "modules": ["core"],
            "commands": ["install", "build"],
            "files": ["template.txt"],
        }

        with patch("zuvo.utils.fs_utils.read_json_safe", return_value=project_data):
            importlib.reload(zuvo.core.project)

            assert zuvo.core.project.NAME == "my-tool"
            assert zuvo.core.project.EXECUTABLE_NAME == "tool-cli"
            assert zuvo.core.project.TITLE == "My Custom Tool"
            assert zuvo.core.project.VERSION == "1.5.0"
            assert zuvo.core.project.DESCRIPTION == "Una herramienta increíble"
            assert zuvo.core.project.AUTHOR == "Wipo"
            assert zuvo.core.project.COPYRIGHT == "2026 Wipo"
            assert zuvo.core.project.APP_TYPE == "standard"
            assert zuvo.core.project.MODULES == ["core"]
            assert zuvo.core.project.COMMANDS_CONFIG == ["install", "build"]
            assert zuvo.core.project.FILES == ["template.txt"]

    def test_project_module_app_type(self):
        """Verify correct loading when APP_TYPE is 'module' and commands is a dictionary."""
        commands_map = {
            "sub_app_1": ["init", "start"],
            "sub_app_2": ["status"],
        }

        project_data = {
            "name": "multi-app",
            "type": "module",
            "commands": commands_map,
        }

        with patch("zuvo.utils.fs_utils.read_json_safe", return_value=project_data):
            importlib.reload(zuvo.core.project)

            assert zuvo.core.project.NAME == "multi-app"
            assert zuvo.core.project.EXECUTABLE_NAME == "multi-app"
            assert zuvo.core.project.APP_TYPE == "module"
            assert zuvo.core.project.COMMANDS_CONFIG == commands_map

    @classmethod
    def teardown_class(cls):
        """Restore zuvo.core.project to its original state after finishing tests in this module."""
        importlib.reload(zuvo.core.project)