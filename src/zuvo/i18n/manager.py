from pathlib import Path
from typing import Optional
from babel import Locale

from zuvo.utils.json import read_json_safe
from zuvo.i18n.system_fallback import SYSTEM_FALLBACK


class I18nManager:
    """Multi-layered translation manager for internationalization."""

    def __init__(
        self,
        fallback_lang: str = "en",
        locales_dir: Optional[Path] = None,
        lang: Optional[str] = None,
    ):
        self.fallback_lang = fallback_lang
        self.locales_dir = locales_dir
        self.current_lang = lang or self._detect_system_language()

        self._app_fallback: dict[str, str] = {}
        self.translations: dict[str, str] = {}

        self.reload()

    def _detect_system_language(self) -> str:
        """Detects the OS primary language code (2-letter ISO) using Babel."""
        try:
            return Locale.default().language.lower()
        except Exception:
            return self.fallback_lang

    def set_locale_dir(self, locales_dir: Path) -> None:
        """Sets or updates the locales directory and reloads translations."""
        self.locales_dir = locales_dir
        self.reload()

    def set_language(self, lang: str) -> None:
        """Changes the current language and reloads translations."""
        self.current_lang = lang
        self.reload()

    def register_app_fallback(self, fallback_dict: dict[str, str]) -> None:
        """Registers developer-defined default fallback translations."""
        self._app_fallback.update(fallback_dict)
        self.reload()

    def reload(self) -> None:
        """Rebuilds the translation map by combining all layers."""
        merged = SYSTEM_FALLBACK.copy()
        merged.update(self._app_fallback)

        if self.locales_dir:
            loaded_data = read_json_safe(self.locales_dir / f"{self.current_lang}.json")

            # If the system language file does not exist, attempt to load the default fallback language
            if not loaded_data and self.current_lang != self.fallback_lang:
                loaded_data = read_json_safe(self.locales_dir / f"{self.fallback_lang}.json")

            if loaded_data:
                merged.update(loaded_data)

        self.translations = merged

    def t(self, key: str, **kwargs) -> str:
        """Retrieves a translated string by key with support for interpolation variables."""
        text = self.translations.get(key, key)
        if kwargs and isinstance(text, str):
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text


i18n = I18nManager()
t = i18n.t