import json
import pytest
from pathlib import Path
from zuvo.i18n.manager import I18nManager


class TestI18nManager:
    """Test suite for I18nManager."""

    @pytest.fixture
    def mock_locales(self, tmp_path: Path) -> Path:
        """Creates temporary locale files for testing."""
        locales_dir = tmp_path / "locales"
        locales_dir.mkdir()

        en_data = {"welcome": "Welcome {name}", "app_name": "Zuvo App"}
        (locales_dir / "en.json").write_text(json.dumps(en_data), encoding="utf-8")

        es_data = {"welcome": "Bienvenido {name}", "app_name": "Aplicación Zuvo"}
        (locales_dir / "es.json").write_text(json.dumps(es_data), encoding="utf-8")

        return locales_dir

    def test_translation_layer_priority(self, mock_locales: Path):
        """Verify that JSON translations override fallback layers."""
        manager = I18nManager(fallback_lang="en", locales_dir=mock_locales, lang="es")

        assert manager.t("app_name") == "Aplicación Zuvo"
        assert manager.t("welcome", name="Carlos") == "Bienvenido Carlos"

    def test_fallback_to_default_language_when_file_missing(self, mock_locales: Path):
        """Verify fallback to English when requested language (e.g., 'fr') JSON is missing."""
        manager = I18nManager(fallback_lang="en", locales_dir=mock_locales, lang="fr")

        assert manager.t("app_name") == "Zuvo App"

    def test_missing_key_returns_key_itself(self, mock_locales: Path):
        """Verify that requesting a non-existent key returns the key name."""
        manager = I18nManager(fallback_lang="en", locales_dir=mock_locales, lang="en")
        assert manager.t("non_existent_key") == "non_existent_key"

    def test_app_fallback_registration(self):
        """Verify developer registered app fallbacks work when no JSON files are loaded."""
        manager = I18nManager(fallback_lang="en", lang="en")
        manager.register_app_fallback({"custom_err": "Custom Error Occurred"})

        assert manager.t("custom_err") == "Custom Error Occurred"

    def test_change_language_dynamically(self, mock_locales: Path):
        """Verify changing language updates the translation map."""
        manager = I18nManager(fallback_lang="en", locales_dir=mock_locales, lang="en")
        assert manager.t("app_name") == "Zuvo App"

        manager.set_language("es")
        assert manager.t("app_name") == "Aplicación Zuvo"