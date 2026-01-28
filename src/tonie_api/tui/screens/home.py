"""Home view for the Tonie Cloud TUI dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Container, Horizontal
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from tonie_api.tui.app import TonieApp


class HomeView(Container):
    """Home view showing user info and statistics.

    Displays welcome message, user details, and summary stats.
    """

    def compose(self) -> ComposeResult:
        """Compose the home view."""
        app: TonieApp = self.app  # type: ignore[assignment]
        user = app.state.user
        households = app.state.households
        tonies = app.state.tonies

        yield Static("Willkommen bei Tonie Cloud!", classes="home-title")

        with Container(classes="home-section"):
            yield Static("Benutzer", classes="section-title")
            if user:
                yield Static(f"  E-Mail: {user.email}")
                yield Static(f"  UUID:   {user.uuid}")

        with Container(classes="home-section"):
            yield Static("Statistik", classes="section-title")
            with Horizontal():
                yield Static(f"  Haushalte: {len(households)}", classes="home-stat")
                yield Static(f"  Creative Tonies: {len(tonies)}", classes="home-stat")

            if tonies:
                total_chapters = sum(t.chapters_present for t in tonies)
                total_duration = sum(t.seconds_present for t in tonies)
                total_remaining = sum(t.seconds_remaining for t in tonies)

                yield Static("")
                yield Static(f"  Kapitel gesamt: {total_chapters}")
                yield Static(f"  Gesamtdauer: {self._format_duration(total_duration)}")
                yield Static(f"  Freier Speicher: {self._format_duration(total_remaining)}")

        with Container(classes="home-section"):
            yield Static("Tastenkürzel", classes="section-title")
            yield Static("  1-5    Navigation")
            yield Static("  R      Daten aktualisieren")
            yield Static("  Q      Logout")
            yield Static("  ?      Hilfe")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to human readable format.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted duration string.
        """
        hours = int(seconds) // 3600
        minutes = (int(seconds) % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
