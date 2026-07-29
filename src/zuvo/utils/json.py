import json
from pathlib import Path
from typing import Any, Optional


def read_json(path: Path) -> Any:
    """
    Safely reads and parses a JSON file.
    Raises FileNotFoundError if the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Required configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_json_safe(path: Path) -> Optional[dict]:
    """
    Attempts to safely read a JSON file. If the file does not exist,
    is not a valid JSON, or reading fails, silently returns None.
    Ideal for optional loads such as i18n files.
    """
    try:
        data = read_json(path)
        return data if isinstance(data, dict) else None
    except Exception:
        return None