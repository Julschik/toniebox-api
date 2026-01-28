"""Settings screen showing configuration and API status."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from tonie_api.exceptions import TonieAPIError

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.binding import BindingType

    from tonie_api.models import Config
    from tonie_api.tui.app import TonieApp

logger = logging.getLogger(__name__)


class SettingsScreen(Screen):
    """Screen showing backend configuration and API status.

    Displays API limits, supported formats, and connection health.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("r", "refresh", "Aktualisieren"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        with Vertical():
            # Configuration section
            with Container(classes="settings-section"):
                yield Static("Backend-Konfiguration", classes="settings-title")
                yield Static("", id="config-content")

            # Status section
            with Container(classes="settings-section"):
                yield Static("API-Status", classes="settings-title")
                yield Static("", id="status-indicator")
                yield Button("Status prüfen", id="check-status-button", variant="default")

    def on_mount(self) -> None:
        """Load configuration on mount."""
        self._load_config()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "check-status-button":
            self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh configuration and status."""
        self._load_config()
        self._check_status()

    @work(thread=True)
    def _load_config(self) -> None:
        """Load configuration in background."""
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api:
            return

        try:
            config = app.state.api.get_config()
            app.call_from_thread(self._display_config, config)
        except TonieAPIError as e:
            app.call_from_thread(
                self._display_config_error,
                str(e),
            )

    def _display_config(self, config: Config) -> None:
        """Display configuration.

        Args:
            config: Configuration data.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.config = config

        minutes = config.max_seconds // 60
        mb = config.max_bytes / (1024 * 1024)

        content = f"""Max. Kapitel:    {config.max_chapters}
Max. Dauer:      {minutes} Minuten ({config.max_seconds}s)
Max. Dateigröße: {mb:.0f} MB
Formate:         {', '.join(config.accepts)}
Sprachen:        {', '.join(config.locales)}"""

        self.query_one("#config-content", Static).update(content)

    def _display_config_error(self, error: str) -> None:
        """Display configuration error.

        Args:
            error: Error message.
        """
        self.query_one("#config-content", Static).update(
            f"Fehler beim Laden der Konfiguration: {error}",
        )

    @work(thread=True)
    def _check_status(self) -> None:
        """Check API status in background."""
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api:
            return

        status_widget = self.query_one("#status-indicator", Static)
        app.call_from_thread(status_widget.update, "Prüfe Verbindung...")

        try:
            start = time.time()
            app.state.api.get_me()
            latency = (time.time() - start) * 1000

            app.call_from_thread(
                self._display_status_ok,
                latency,
            )
        except TonieAPIError as e:
            app.call_from_thread(
                self._display_status_error,
                str(e),
            )

    def _display_status_ok(self, latency: float) -> None:
        """Display successful status.

        Args:
            latency: Response latency in milliseconds.
        """
        status_widget = self.query_one("#status-indicator", Static)
        status_widget.update(f"[green]Verbunden[/green] (Latenz: {latency:.0f}ms)")

    def _display_status_error(self, error: str) -> None:
        """Display status error.

        Args:
            error: Error message.
        """
        status_widget = self.query_one("#status-indicator", Static)
        status_widget.update(f"[red]Nicht erreichbar:[/red] {error}")
