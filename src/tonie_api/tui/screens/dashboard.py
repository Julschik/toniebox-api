"""Dashboard screen - main container with sidebar navigation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static

from tonie_api.exceptions import AuthenticationError, TonieAPIError
from tonie_api.tui.screens.home import HomeView
from tonie_api.tui.screens.presets import PresetsScreen
from tonie_api.tui.screens.settings import SettingsScreen
from tonie_api.tui.screens.tonies import ToniesScreen
from tonie_api.tui.screens.upload import UploadScreen
from tonie_api.tui.widgets.error_modal import ConfirmModal, ErrorModal
from tonie_api.tui.widgets.sidebar import Sidebar

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.binding import BindingType

    from tonie_api.tui.app import TonieApp

logger = logging.getLogger(__name__)

CREDENTIALS_FILE = Path.home() / ".config" / "tonie-api" / "credentials"


class DashboardScreen(Screen):
    """Main dashboard screen with sidebar navigation.

    Contains sidebar for navigation and content area for views.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("1", "nav_home", "Home"),
        ("2", "nav_tonies", "Tonies"),
        ("3", "nav_upload", "Upload"),
        ("4", "nav_presets", "Presets"),
        ("5", "nav_settings", "Einstellungen"),
        ("q", "logout", "Logout"),
        ("r", "refresh", "Aktualisieren"),
        ("question_mark", "help", "Hilfe"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize dashboard screen."""
        super().__init__(name=name, id=id, classes=classes)
        self._current_view = "home"

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        app: TonieApp = self.app  # type: ignore[assignment]
        user_email = app.state.user.email if app.state.user else ""

        # Header
        with Horizontal(id="dashboard-header"):
            yield Static("Tonie Cloud", id="header-title")
            yield Static(user_email, id="header-user")

        # Main content area
        with Horizontal():
            yield Sidebar(id="dashboard-sidebar")
            with Container(id="dashboard-content"):
                yield HomeView(id="view-home")

        # Footer
        yield Static(
            "1-5: Navigation | R: Aktualisieren | Q: Logout | ?: Hilfe",
            id="dashboard-footer",
        )

    def on_mount(self) -> None:
        """Load initial data on mount."""
        self._load_initial_data()

    def on_sidebar_navigate(self, event: Sidebar.Navigate) -> None:
        """Handle sidebar navigation."""
        self._switch_view(event.view_id)

    def on_sidebar_logout(self, _event: Sidebar.Logout) -> None:
        """Handle logout from sidebar."""
        self.action_logout()

    def _switch_view(self, view_id: str) -> None:
        """Switch to a different view.

        Args:
            view_id: ID of view to switch to.
        """
        if view_id == self._current_view:
            return

        self._current_view = view_id

        # Update sidebar active state
        sidebar = self.query_one(Sidebar)
        sidebar.set_active(view_id)

        # Replace content
        content = self.query_one("#dashboard-content", Container)
        content.remove_children()

        if view_id == "home":
            content.mount(HomeView(id="view-home"))
        elif view_id == "tonies":
            content.mount(ToniesScreen(id="view-tonies"))
        elif view_id == "upload":
            content.mount(UploadScreen(id="view-upload"))
        elif view_id == "presets":
            content.mount(PresetsScreen(id="view-presets"))
        elif view_id == "settings":
            content.mount(SettingsScreen(id="view-settings"))

    # Navigation actions
    def action_nav_home(self) -> None:
        """Navigate to home view."""
        self._switch_view("home")

    def action_nav_tonies(self) -> None:
        """Navigate to tonies view."""
        self._switch_view("tonies")

    def action_nav_upload(self) -> None:
        """Navigate to upload view."""
        self._switch_view("upload")

    def action_nav_presets(self) -> None:
        """Navigate to presets view."""
        self._switch_view("presets")

    def action_nav_settings(self) -> None:
        """Navigate to settings view."""
        self._switch_view("settings")

    def action_logout(self) -> None:
        """Handle logout action."""
        def handle_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._do_logout()

        self.app.push_screen(
            ConfirmModal("Möchtest du dich wirklich ausloggen?", title="Logout"),
            handle_confirm,
        )

    def _do_logout(self) -> None:
        """Perform logout."""
        app: TonieApp = self.app  # type: ignore[assignment]

        # Delete credentials file
        if CREDENTIALS_FILE.exists():
            CREDENTIALS_FILE.unlink()

        # Reset state
        app.state.reset()

        # Return to login
        app.switch_screen("login")
        self.notify("Erfolgreich ausgeloggt")

    def action_refresh(self) -> None:
        """Refresh current data."""
        self._load_data()

    def action_help(self) -> None:
        """Show help dialog."""
        help_text = """Tastenkürzel:

Navigation:
  1       Home
  2       Tonies
  3       Upload
  4       Presets
  5       Einstellungen

Aktionen:
  R       Daten aktualisieren
  S       Kapitel mischen (Tonies-Ansicht)
  C       Kapitel löschen (Tonies-Ansicht)
  U       Hochladen
  Q       Logout
  Esc     Abbrechen/Schließen"""

        self.app.push_screen(ErrorModal(help_text, title="Hilfe"))

    @work(exclusive=True, thread=True)
    def _load_initial_data(self) -> None:
        """Load initial data (households and tonies)."""
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api:
            return

        try:
            # Load households
            households = app.state.api.get_households()
            app.call_from_thread(self._on_households_loaded, households)

        except AuthenticationError:
            app.call_from_thread(self._handle_auth_error)
        except TonieAPIError as e:
            app.call_from_thread(
                self.app.push_screen,
                ErrorModal(f"Fehler beim Laden: {e}"),
            )

    def _on_households_loaded(self, households: list) -> None:
        """Handle loaded households.

        Args:
            households: List of households.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.households = households
        app.state.apply_saved_household()

        if app.state.current_household_id:
            self._load_tonies()

    @work(thread=True)
    def _load_tonies(self) -> None:
        """Load tonies for current household."""
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api or not app.state.current_household_id:
            return

        try:
            tonies = app.state.api.get_creative_tonies(app.state.current_household_id)
            app.call_from_thread(self._on_tonies_loaded, tonies)
        except AuthenticationError:
            app.call_from_thread(self._handle_auth_error)
        except TonieAPIError as e:
            app.call_from_thread(
                self.app.push_screen,
                ErrorModal(f"Fehler beim Laden der Tonies: {e}"),
            )

    def _on_tonies_loaded(self, tonies: list) -> None:
        """Handle loaded tonies.

        Args:
            tonies: List of tonies.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.tonies = tonies

        # Refresh home view if active
        if self._current_view == "home":
            content = self.query_one("#dashboard-content", Container)
            content.remove_children()
            content.mount(HomeView(id="view-home"))

    @work(thread=True)
    def _load_data(self) -> None:
        """Reload all data."""
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api:
            return

        try:
            households = app.state.api.get_households()
            app.call_from_thread(setattr, app.state, "households", households)

            if app.state.current_household_id:
                tonies = app.state.api.get_creative_tonies(app.state.current_household_id)
                app.call_from_thread(self._on_tonies_loaded, tonies)

            app.call_from_thread(self.notify, "Daten aktualisiert")

        except AuthenticationError:
            app.call_from_thread(self._handle_auth_error)
        except TonieAPIError as e:
            app.call_from_thread(
                self.app.push_screen,
                ErrorModal(f"Fehler beim Aktualisieren: {e}"),
            )

    def _handle_auth_error(self) -> None:
        """Handle authentication error."""
        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.reset()
        app.switch_screen("login")
        app.push_screen(ErrorModal("Session abgelaufen. Bitte erneut anmelden."))
