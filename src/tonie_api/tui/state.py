"""Application state management for the Tonie Cloud TUI."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tonie_api.api import TonieAPI
    from tonie_api.models import Config, CreativeTonie, Household, User

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "tonie-api"
PREFERENCES_FILE = CONFIG_DIR / "preferences.json"
CREDENTIALS_FILE = CONFIG_DIR / "credentials"


class AppState:
    """Centralized application state.

    Manages authentication state, API data, and user preferences.
    """

    def __init__(self) -> None:
        """Initialize application state."""
        self.is_authenticated: bool = False
        self.user: User | None = None
        self.households: list[Household] = []
        self.current_household_id: str | None = None
        self.tonies: list[CreativeTonie] = []
        self.config: Config | None = None
        self.is_loading: bool = False
        self.api: TonieAPI | None = None
        self._saved_household_id: str | None = None
        self._load_preferences()

    def _load_preferences(self) -> None:
        """Load user preferences from config file."""
        if PREFERENCES_FILE.exists():
            try:
                prefs = json.loads(PREFERENCES_FILE.read_text(encoding="utf-8"))
                self._saved_household_id = prefs.get("last_household_id")
                logger.debug("Loaded preferences: household=%s", self._saved_household_id)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load preferences: %s", e)
                self._saved_household_id = None
        else:
            self._saved_household_id = None

    def save_preferences(self) -> None:
        """Save user preferences to config file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            prefs = {"last_household_id": self.current_household_id}
            PREFERENCES_FILE.write_text(json.dumps(prefs), encoding="utf-8")
            logger.debug("Saved preferences: household=%s", self.current_household_id)
        except OSError as e:
            logger.warning("Failed to save preferences: %s", e)

    def apply_saved_household(self) -> None:
        """Apply saved household preference if valid."""
        if self._saved_household_id and self.households:
            # Verify saved household still exists
            valid_ids = {h.id for h in self.households}
            if self._saved_household_id in valid_ids:
                self.current_household_id = self._saved_household_id
                return
        # Fall back to first household
        if self.households:
            self.current_household_id = self.households[0].id

    @staticmethod
    def has_saved_credentials() -> bool:
        """Check if credentials file exists."""
        return CREDENTIALS_FILE.exists()

    def reset(self) -> None:
        """Reset all state (for logout)."""
        self.is_authenticated = False
        self.user = None
        self.households = []
        self.current_household_id = None
        self.tonies = []
        self.config = None
        self.api = None
