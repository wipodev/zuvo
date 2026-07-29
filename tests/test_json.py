import json
import pytest
from pathlib import Path
from zuvo.utils.json import read_json, read_json_safe


class TestReadJson:
    """Test suite for read_json function."""

    def test_read_json_success(self, tmp_path: Path):
        """Verify that a valid JSON file is read and parsed correctly."""
        json_file = tmp_path / "valid.json"
        content = {"name": "Zuvo", "version": "1.0.0"}
        json_file.write_text(json.dumps(content), encoding="utf-8")

        result = read_json(json_file)

        assert result == content

    def test_read_json_file_not_found(self, tmp_path: Path):
        """Verify that FileNotFoundError is raised when the file does not exist."""
        non_existent_file = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError) as exc_info:
            read_json(non_existent_file)

        assert "not found" in str(exc_info.value)

    def test_read_json_invalid_syntax(self, tmp_path: Path):
        """Verify that json.JSONDecodeError is raised for malformed JSON."""
        corrupted_file = tmp_path / "corrupted.json"
        corrupted_file.write_text("{ invalid_json: ", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            read_json(corrupted_file)


class TestReadJsonSafe:
    """Test suite for read_json_safe function."""

    def test_read_json_safe_success(self, tmp_path: Path):
        """Verify that a valid dictionary JSON returns the parsed dictionary."""
        json_file = tmp_path / "valid.json"
        content = {"key": "value"}
        json_file.write_text(json.dumps(content), encoding="utf-8")

        assert read_json_safe(json_file) == content

    def test_read_json_safe_missing_file_returns_none(self, tmp_path: Path):
        """Verify that None is returned when the file does not exist."""
        non_existent_file = tmp_path / "missing.json"
        assert read_json_safe(non_existent_file) is None

    def test_read_json_safe_corrupted_json_returns_none(self, tmp_path: Path):
        """Verify that None is returned when the JSON file is corrupted."""
        corrupted_file = tmp_path / "corrupted.json"
        corrupted_file.write_text("not a json", encoding="utf-8")

        assert read_json_safe(corrupted_file) is None

    def test_read_json_safe_non_dict_json_returns_none(self, tmp_path: Path):
        """
        Verify that None is returned when the JSON contains valid data
        that is NOT a dictionary (e.g. a list or integer).
        """
        list_json = tmp_path / "list.json"
        list_json.write_text(json.dumps(["item1", "item2"]), encoding="utf-8")

        assert read_json_safe(list_json) is None