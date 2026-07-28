from pathlib import Path
from zuvo.utils.paths import get_root_dir
from zuvo.utils.fs_utils import read_json_safe

PROJECT_ROOT: Path = get_root_dir()
JSON_PATH: Path = PROJECT_ROOT / "project.json"

_config: dict = read_json_safe(JSON_PATH) or {}

# ---------------------------------------------------------------------------
#               Application Metadata Interface
# ---------------------------------------------------------------------------
NAME: str = _config.get("name", "cli-app")
EXECUTABLE_NAME: str = _config.get("executable_name", NAME)
TITLE: str = _config.get("title", NAME)
VERSION: str = _config.get("version", "0.0.1")
DESCRIPTION: str = _config.get("description", "")
AUTHOR: str = _config.get("author", "")
COPYRIGHT: str = _config.get("copyright", "")

# Configuración de Comandos y Módulos
APP_TYPE: str = _config.get("type", "standard")
MODULES: list[str] = _config.get("modules", [])
COMMANDS_CONFIG = _config.get("commands", [] if APP_TYPE == "standard" else {})

# Additional files (Assets, Templates, etc.)
FILES: list[str] = _config.get("files", [])