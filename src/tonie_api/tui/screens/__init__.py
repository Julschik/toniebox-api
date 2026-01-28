"""TUI screens for the Tonie Cloud application."""

from __future__ import annotations

from tonie_api.tui.screens.dashboard import DashboardScreen
from tonie_api.tui.screens.home import HomeView
from tonie_api.tui.screens.login import LoginScreen
from tonie_api.tui.screens.presets import PresetsScreen
from tonie_api.tui.screens.settings import SettingsScreen
from tonie_api.tui.screens.tonies import ToniesScreen
from tonie_api.tui.screens.upload import UploadScreen

__all__ = [
    "DashboardScreen",
    "HomeView",
    "LoginScreen",
    "PresetsScreen",
    "SettingsScreen",
    "ToniesScreen",
    "UploadScreen",
]
