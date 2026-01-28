"""Tests for the i18n module."""

from __future__ import annotations

from tonie_api.cli.i18n import get_locale, load_locale, t


class TestLoadLocale:
    """Tests for load_locale function."""

    def test_load_german_locale(self):
        """Test loading German locale."""
        load_locale("de")
        assert get_locale() == "de"

    def test_load_english_locale(self):
        """Test loading English locale."""
        load_locale("en")
        assert get_locale() == "en"

    def test_load_default_locale(self):
        """Test loading default locale."""
        load_locale()
        assert get_locale() == "de"

    def test_load_invalid_locale_falls_back(self):
        """Test that invalid locale falls back to German."""
        load_locale("invalid")
        assert get_locale() == "de"


class TestTranslate:
    """Tests for t function."""

    def test_translate_simple_key(self):
        """Test translating a simple key."""
        load_locale("de")
        result = t("cli.me.help")
        assert result == "Zeigt deine Kontoinformationen"

    def test_translate_english(self):
        """Test translating to English."""
        load_locale("en")
        result = t("cli.me.help")
        assert result == "Show your account information"

    def test_translate_with_format_args(self):
        """Test translating with format arguments."""
        load_locale("de")
        result = t("cli.upload.uploading", filename="test.mp3")
        assert result == "Lade test.mp3 hoch..."

    def test_translate_missing_key(self):
        """Test that missing key returns the key itself."""
        load_locale("de")
        result = t("nonexistent.key")
        assert result == "nonexistent.key"

    def test_translate_nested_key(self):
        """Test translating deeply nested key."""
        load_locale("de")
        result = t("cli.preset.list.empty")
        assert result == "Keine Presets gefunden."

    def test_translate_auto_loads_locale(self):
        """Test that translation auto-loads locale if not loaded."""
        # Reset state by patching
        from tonie_api.cli import i18n

        i18n._loaded = False
        i18n._translations = {}

        # Should auto-load and translate
        result = t("cli.me.help")
        assert "Kontoinformationen" in result or "account information" in result.lower()

    def test_translate_missing_format_key(self):
        """Test translation with missing format key."""
        load_locale("de")
        # Should return the template string without the missing key replaced
        result = t("cli.upload.uploading")
        assert "filename" in result or "{" in result or result == "cli.upload.uploading"


class TestGetLocale:
    """Tests for get_locale function."""

    def test_get_locale_after_load(self):
        """Test get_locale returns current locale."""
        load_locale("en")
        assert get_locale() == "en"

        load_locale("de")
        assert get_locale() == "de"
