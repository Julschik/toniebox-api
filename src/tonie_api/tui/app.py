"""Main Textual application for the Tonie Cloud TUI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import ClassVar

from textual.app import App

from tonie_api import TonieAPI
from tonie_api.exceptions import AuthenticationError
from tonie_api.tui.screens.dashboard import DashboardScreen
from tonie_api.tui.screens.login import LoginScreen
from tonie_api.tui.state import AppState

logger = logging.getLogger(__name__)

# Path to CSS file
_CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"


class TonieApp(App):
    """Main Tonie Cloud TUI application.

    Provides an interactive terminal interface for managing Creative Tonies.
    """

    TITLE = "Tonie Cloud"
    SUB_TITLE = "Creative Tonie Manager"

    # Load CSS from file
    CSS_PATH = _CSS_PATH

    # Screen bindings
    SCREENS: ClassVar[dict] = {
        "login": LoginScreen,
        "dashboard": DashboardScreen,
    }

    def __init__(self) -> None:
        """Initialize the application."""
        super().__init__()
        self.state = AppState()

    def on_mount(self) -> None:
        """Handle application mount.

        Checks for saved credentials and auto-logs in if available.
        """
        if self.state.has_saved_credentials():
            self._try_auto_login()
        else:
            self.push_screen("login")

    def _try_auto_login(self) -> None:
        """Attempt auto-login with saved credentials."""
        try:
            api = TonieAPI()
            user = api.get_me()

            self.state.api = api
            self.state.user = user
            self.state.is_authenticated = True

            logger.info("Auto-login successful: %s", user.email)
            self.push_screen("dashboard")

        except AuthenticationError:
            logger.info("Auto-login failed, showing login screen")
            self.push_screen("login")
        except Exception as e:  # noqa: BLE001
            logger.warning("Auto-login error: %s", e)
            self.push_screen("login")
