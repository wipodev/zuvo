from pathlib import Path
from typing import Optional
from babel import Locale

from zuvo.utils.json import read_json_safe
from zuvo.i18n.system_fallback import SYSTEM_FALLBACK
ZUVO_LOCALES_DIR = Path(__file__).parent.parent / "locales"


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

    def _load_layered_json(self, base_dir: Path) -> dict[str, str]:
        """Loads translations from a directory.

        If current_lang is different from fallback_lang, it loads the fallback
        first and overrides it with current_lang values.
        """
        data: dict[str, str] = {}

        fallback_file = base_dir / f"{self.fallback_lang}.json"
        data.update(read_json_safe(fallback_file))

        if self.current_lang != self.fallback_lang:
            current_file = base_dir / f"{self.current_lang}.json"
            if current_file.is_file():
                data.update(read_json_safe(current_file))

        return data

    def reload(self) -> None:
        """Rebuilds the translation map by combining all layers in priority order:

        1. SYSTEM_FALLBACK (hardcoded dict)
        2. Zuvo internal locales (fallback_lang -> current_lang)
        3. Developer app fallback dict
        4. User app locales directory (fallback_lang -> current_lang)
        """
        merged = SYSTEM_FALLBACK.copy()
        merged.update(self._load_layered_json(ZUVO_LOCALES_DIR))
        merged.update(self._app_fallback)

        if self.locales_dir and self.locales_dir.is_dir():
            merged.update(self._load_layered_json(self.locales_dir))

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