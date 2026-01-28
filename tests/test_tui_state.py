"""Tests for TUI state management."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

from tonie_api.tui.state import AppState


class TestAppStateInit:
    """Tests for AppState initialization."""

    def test_init_defaults(self) -> None:
        """Test default values after initialization."""
        state = AppState()

        assert state.is_authenticated is False
        assert state.user is None
        assert state.households == []
        assert state.tonies == []
        assert state.config is None
        assert state.is_loading is False
        assert state.api is None

    def test_init_loads_preferences(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that init loads saved preferences."""
        prefs_file = tmp_path / "preferences.json"
        prefs_file.write_text('{"last_household_id": "test-household-123"}')

        monkeypatch.setattr("tonie_api.tui.state.PREFERENCES_FILE", prefs_file)
        state = AppState()

        assert state._saved_household_id == "test-household-123"

    def test_init_handles_missing_preferences(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing preferences file is handled gracefully."""
        prefs_file = tmp_path / "nonexistent" / "preferences.json"
        monkeypatch.setattr("tonie_api.tui.state.PREFERENCES_FILE", prefs_file)

        state = AppState()

        assert state._saved_household_id is None

    def test_init_handles_invalid_preferences_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that invalid JSON in preferences file is handled gracefully."""
        prefs_file = tmp_path / "preferences.json"
        prefs_file.write_text("not valid json")

        monkeypatch.setattr("tonie_api.tui.state.PREFERENCES_FILE", prefs_file)
        state = AppState()

        assert state._saved_household_id is None


class TestAppStatePreferences:
    """Tests for preference saving/loading."""

    def test_save_preferences(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test saving preferences to file."""
        config_dir = tmp_path / "config"
        prefs_file = config_dir / "preferences.json"

        monkeypatch.setattr("tonie_api.tui.state.CONFIG_DIR", config_dir)
        monkeypatch.setattr("tonie_api.tui.state.PREFERENCES_FILE", prefs_file)

        state = AppState()
        state.current_household_id = "new-household-456"
        state.save_preferences()

        assert prefs_file.exists()
        saved_prefs = json.loads(prefs_file.read_text())
        assert saved_prefs["last_household_id"] == "new-household-456"

    def test_save_preferences_creates_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that save_preferences creates config directory if needed."""
        config_dir = tmp_path / "new_config_dir"
        prefs_file = config_dir / "preferences.json"

        monkeypatch.setattr("tonie_api.tui.state.CONFIG_DIR", config_dir)
        monkeypatch.setattr("tonie_api.tui.state.PREFERENCES_FILE", prefs_file)

        state = AppState()
        state.current_household_id = "test-id"
        state.save_preferences()

        assert config_dir.exists()
        assert prefs_file.exists()


class TestAppStateHousehold:
    """Tests for household selection."""

    def test_apply_saved_household_with_valid_id(self) -> None:
        """Test applying a valid saved household ID."""
        state = AppState()
        state._saved_household_id = "household-2"

        # Create mock households
        h1 = MagicMock()
        h1.id = "household-1"
        h2 = MagicMock()
        h2.id = "household-2"
        state.households = [h1, h2]

        state.apply_saved_household()

        assert state.current_household_id == "household-2"

    def test_apply_saved_household_with_invalid_id(self) -> None:
        """Test that invalid saved household ID falls back to first household."""
        state = AppState()
        state._saved_household_id = "nonexistent-household"

        h1 = MagicMock()
        h1.id = "household-1"
        state.households = [h1]

        state.apply_saved_household()

        assert state.current_household_id == "household-1"

    def test_apply_saved_household_no_saved_id(self) -> None:
        """Test that no saved ID uses first household."""
        state = AppState()
        state._saved_household_id = None

        h1 = MagicMock()
        h1.id = "household-1"
        h2 = MagicMock()
        h2.id = "household-2"
        state.households = [h1, h2]

        state.apply_saved_household()

        assert state.current_household_id == "household-1"

    def test_apply_saved_household_no_households(self) -> None:
        """Test behavior when no households exist."""
        state = AppState()
        state._saved_household_id = "some-id"
        state.households = []

        state.apply_saved_household()

        assert state.current_household_id is None


class TestAppStateCredentials:
    """Tests for credentials checking."""

    def test_has_saved_credentials_true(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test has_saved_credentials returns True when file exists."""
        creds_file = tmp_path / "credentials"
        creds_file.write_text("test@example.com\nsecret")

        monkeypatch.setattr("tonie_api.tui.state.CREDENTIALS_FILE", creds_file)

        assert AppState.has_saved_credentials() is True

    def test_has_saved_credentials_false(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test has_saved_credentials returns False when file doesn't exist."""
        creds_file = tmp_path / "nonexistent_credentials"

        monkeypatch.setattr("tonie_api.tui.state.CREDENTIALS_FILE", creds_file)

        assert AppState.has_saved_credentials() is False


class TestAppStateReset:
    """Tests for state reset."""

    def test_reset_clears_all_state(self) -> None:
        """Test that reset clears all state values."""
        state = AppState()
        state.is_authenticated = True
        state.user = MagicMock()
        state.households = [MagicMock()]
        state.current_household_id = "test-id"
        state.tonies = [MagicMock()]
        state.config = MagicMock()
        state.api = MagicMock()

        state.reset()

        assert state.is_authenticated is False
        assert state.user is None
        assert state.households == []
        assert state.current_household_id is None
        assert state.tonies == []
        assert state.config is None
        assert state.api is None
