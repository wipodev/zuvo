import json
import pytest
from unittest.mock import patch

from zuvo.utils.fs_utils import read_json, read_json_safe


class TestReadJson:
    """Test suite for strict JSON reading (read_json)."""

    def test_read_json_success(self, tmp_path):
        """Verify that a valid JSON file is read and parsed correctly."""
        json_file = tmp_path / "config.json"
        content = {"name": "python-cli", "version": "1.0.0"}
        json_file.write_text(json.dumps(content), encoding="utf-8")

        result = read_json(json_file)

        assert result == content

    def test_read_json_file_not_found_with_i18n(self, tmp_path, set_language):
        """Verify that it raises FileNotFoundError with the translated message when the file does not exist."""
        set_language("es")
        non_existent_file = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError) as exc_info:
            read_json(non_existent_file)

        assert str(non_existent_file) in str(exc_info.value)

    def test_read_json_file_not_found_fallback(self, tmp_path):
        """Verify that it uses the fallback message if importing/translating i18n fails."""
        non_existent_file = tmp_path / "missing.json"

        # Simulate a failure when importing t from app.i18n
        with patch("zuvo.i18n.t", side_effect=Exception("i18n Error")):
            with pytest.raises(FileNotFoundError) as exc_info:
                read_json(non_existent_file)

            assert "Required configuration file not found at:" in str(exc_info.value)

    def test_read_json_invalid_syntax(self, tmp_path):
        """Verify that it propagates json.JSONDecodeError if the content is not valid JSON."""
        invalid_json_file = tmp_path / "corrupt.json"
        invalid_json_file.write_text("{invalid_json: true,", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            read_json(invalid_json_file)


class TestReadJsonSafe:
    """Test suite for safe/optional JSON reading (read_json_safe)."""

    def test_read_json_safe_success(self, tmp_path):
        """Verify that it returns the dictionary if the JSON is valid."""
        json_file = tmp_path / "valid.json"
        data = {"key": "value"}
        json_file.write_text(json.dumps(data), encoding="utf-8")

        result = read_json_safe(json_file)

        assert result == data

    def test_read_json_safe_file_not_exists(self, tmp_path):
        """Verify that it silently returns None if the file does not exist."""
        missing_file = tmp_path / "does_not_exist.json"

        result = read_json_safe(missing_file)

        assert result is None

    def test_read_json_safe_not_a_dict(self, tmp_path):
        """Verify that it returns None if the root JSON is a list or a type other than dict."""
        list_json_file = tmp_path / "list.json"
        list_json_file.write_text(json.dumps(["item1", "item2"]), encoding="utf-8")

        result = read_json_safe(list_json_file)

        assert result is None

    def test_read_json_safe_corrupt_file(self, tmp_path):
        """Verify that it silently returns None if the JSON is malformed or a read error occurs."""
        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("NOT A JSON CONTENT", encoding="utf-8")

        result = read_json_safe(corrupt_file)

        assert result is None