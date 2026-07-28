import json
from unittest.mock import patch, MagicMock

from zuvo.i18n.manager import I18nManager


class TestI18nLanguageDetection:
    """Tests for system language detection and default fallbacks."""

    def test_detect_system_language_success(self, tmp_path):
        """Verify that Babel correctly detects the primary OS language in lowercase."""
        mock_locale = MagicMock()
        mock_locale.language = "ES"

        with patch("babel.Locale.default", return_value=mock_locale), \
             patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager(fallback_lang="en")
            assert manager.current_lang == "es"

    def test_detect_system_language_exception_fallback(self, tmp_path):
        """Verify that if Babel raises an exception, fallback_lang is used."""
        with patch("babel.Locale.default", side_effect=Exception("Babel error")), \
             patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager(fallback_lang="en")
            assert manager.current_lang == "en"


class TestI18nManagerLayers:
    """Tests for the layer hierarchy and translation overrides."""

    def test_system_fallback_layer(self, tmp_path):
        """Verify that SYSTEM_FALLBACK is present by default."""
        with patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager()
            # A known key in SYSTEM_FALLBACK
            assert "cli_error_args_title" in manager.translations

    def test_app_fallback_overrides_system_fallback(self, tmp_path):
        """Verify that register_app_fallback overrides base translations and triggers a reload."""
        with patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager()
            manager.register_app_fallback({
                "cli_error_args_title": "Título Sobrescrito",
                "custom_app_key": "Mi clave de App"
            })

            assert manager.translations["cli_error_args_title"] == "Título Sobrescrito"
            assert manager.translations["custom_app_key"] == "Mi clave de App"

    def test_json_file_overrides_all_layers(self, tmp_path):
        """Verify that the JSON file for the system language has the highest priority."""
        # Create es.json in the temporary locales directory
        es_file = tmp_path / "es.json"
        es_file.write_text(json.dumps({
            "cli_error_args_title": "Título Desde JSON",
            "json_key": "Valor JSON"
        }), encoding="utf-8")

        mock_locale = MagicMock()
        mock_locale.language = "es"

        with patch("babel.Locale.default", return_value=mock_locale), \
             patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager()

            assert manager.translations["cli_error_args_title"] == "Título Desde JSON"
            assert manager.translations["json_key"] == "Valor JSON"

    def test_fallback_to_fallback_lang_json_if_current_lang_missing(self, tmp_path):
        """
        Verify that if the JSON file for the detected language (e.g., 'fr.json') does not exist,
        it attempts to load the fallback language JSON (e.g., 'en.json').
        """
        en_file = tmp_path / "en.json"
        en_file.write_text(json.dumps({
            "fallback_json_key": "English Value"
        }), encoding="utf-8")

        mock_locale = MagicMock()
        mock_locale.language = "fr"  # Language without an existing fr.json

        with patch("babel.Locale.default", return_value=mock_locale), \
             patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager(fallback_lang="en")

            assert manager.translations["fallback_json_key"] == "English Value"


class TestI18nTranslationFormatting:
    """Tests for the t() function regarding text retrieval and interpolation."""

    def test_t_simple_retrieval(self, tmp_path):
        """Verify direct text retrieval."""
        with patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager()
            manager.register_app_fallback({"hello": "Hola Mundo"})

            assert manager.t("hello") == "Hola Mundo"

    def test_t_returns_key_if_not_found(self, tmp_path):
        """Verify that it returns the key itself if no translation exists."""
        with patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager()

            assert manager.t("non_existent_key") == "non_existent_key"

    def test_t_interpolation_success(self, tmp_path):
        """Verify that placeholders marked with {var} are replaced correctly."""
        with patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager()
            manager.register_app_fallback({"welcome": "Hola {name}, bienvenido a {app}"})

            result = manager.t("welcome", name="Wipo", app="CLI")
            assert result == "Hola Wipo, bienvenido a CLI"

    def test_t_interpolation_key_error_handling(self, tmp_path):
        """Verify that if interpolation parameters are missing (KeyError), it returns the unformatted template."""
        with patch("zuvo.i18n.manager.get_locales_dir", return_value=tmp_path):
            manager = I18nManager()
            manager.register_app_fallback({"welcome": "Hola {name}, bienvenido a {app}"})

            # Deliberately omitting the 'app' parameter
            result = manager.t("welcome", name="Wipo")
            assert result == "Hola {name}, bienvenido a {app}"