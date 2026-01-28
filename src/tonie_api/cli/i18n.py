"""Internationalization support for the CLI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_current_locale: str = "de"
_translations: dict[str, Any] = {}
_loaded: bool = False


def load_locale(locale: str = "de") -> None:
    """Load translations for the specified locale.

    Args:
        locale: Language code (de or en). Defaults to German.
    """
    global _translations, _current_locale, _loaded  # noqa: PLW0603

    locale_file = Path(__file__).parent / "locales" / f"{locale}.yaml"

    if not locale_file.exists():
        logger.warning("Locale file not found: %s, falling back to 'de'", locale_file)
        locale_file = Path(__file__).parent / "locales" / "de.yaml"
        locale = "de"

    try:
        _translations = yaml.safe_load(locale_file.read_text(encoding="utf-8")) or {}
        _current_locale = locale
        _loaded = True
        logger.debug("Loaded locale: %s", locale)
    except yaml.YAMLError as e:
        logger.warning("Failed to load locale %s: %s", locale, e)
        _translations = {}


def get_locale() -> str:
    """Get the current locale.

    Returns:
        Current locale code.
    """
    return _current_locale


def t(key: str, **kwargs: Any) -> str:
    """Translate a key with optional format arguments.

    Args:
        key: Dot-separated key path (e.g., "cli.me.help").
        **kwargs: Format arguments to substitute in the translation.

    Returns:
        Translated string, or the key itself if not found.
    """
    # Auto-load default locale if not loaded
    if not _loaded:
        load_locale()

    # Navigate nested dict
    parts = key.split(".")
    value: Any = _translations

    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break

    if value is None or not isinstance(value, str):
        logger.debug("Translation not found for key: %s", key)
        return key

    # Format with kwargs if provided
    if kwargs:
        try:
            return value.format(**kwargs)
        except KeyError as e:
            logger.warning("Missing format key %s for translation: %s", e, key)
            return value

    return value
