"""Tonies screen for viewing and managing Creative Tonies."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Select, Static

from tonie_api.exceptions import AuthenticationError, TonieAPIError
from tonie_api.tui.widgets.chapter_list import ChapterList
from tonie_api.tui.widgets.error_modal import ConfirmModal, ErrorModal

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.binding import BindingType

    from tonie_api.models import CreativeTonie
    from tonie_api.tui.app import TonieApp

logger = logging.getLogger(__name__)


class ToniesScreen(Screen):
    """Screen for viewing and managing Creative Tonies.

    Displays list of tonies with details and chapter management.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("r", "refresh", "Aktualisieren"),
        ("s", "shuffle", "Mischen"),
        ("c", "clear", "Löschen"),
        ("u", "upload", "Upload"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize tonies screen."""
        super().__init__(name=name, id=id, classes=classes)
        self._selected_tonie: CreativeTonie | None = None

    def compose(self) -> ComposeResult:
        """Compose the tonies screen."""
        app: TonieApp = self.app  # type: ignore[assignment]

        with Vertical():
            # Header with household selector
            with Horizontal(id="tonies-header"):
                options = [
                    (h.name, h.id)
                    for h in app.state.households
                ]
                yield Select(
                    options,
                    value=app.state.current_household_id,
                    id="household-select",
                    prompt="Haushalt wählen",
                )
                yield Button("Aktualisieren", id="refresh-button", variant="default")

            # Tonies table
            yield DataTable(id="tonies-table")

            # Details panel
            with Container(id="tonie-details"):
                yield Static("Wähle einen Tonie aus der Liste", id="details-title")
                yield ChapterList(id="chapter-list")

            # Action buttons
            with Horizontal(id="tonies-actions"):
                yield Button("[S]huffle", id="shuffle-button", variant="default")
                yield Button("[C]lear", id="clear-button", variant="warning")
                yield Button("[U]pload", id="upload-button", variant="primary")

    def on_mount(self) -> None:
        """Initialize table and load data."""
        table = self.query_one("#tonies-table", DataTable)
        table.add_column("Name", key="name")
        table.add_column("Kapitel", key="chapters")
        table.add_column("Dauer", key="duration")
        table.add_column("Frei", key="remaining")
        table.add_column("Letzte Änderung", key="updated")
        table.cursor_type = "row"

        self._populate_table()

    def _populate_table(self) -> None:
        """Populate the table with tonies data."""
        app: TonieApp = self.app  # type: ignore[assignment]
        table = self.query_one("#tonies-table", DataTable)
        table.clear()

        for tonie in app.state.tonies:
            last_update = (
                tonie.last_update.strftime("%Y-%m-%d")
                if tonie.last_update
                else "-"
            )
            table.add_row(
                tonie.name,
                f"{tonie.chapters_present}/15",
                self._format_duration(tonie.seconds_present),
                self._format_duration(tonie.seconds_remaining),
                last_update,
                key=tonie.id,
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle tonie selection."""
        app: TonieApp = self.app  # type: ignore[assignment]

        tonie_id = event.row_key.value if event.row_key else None
        if not tonie_id:
            return

        # Find selected tonie
        for tonie in app.state.tonies:
            if tonie.id == tonie_id:
                self._selected_tonie = tonie
                self._update_details(tonie)
                break

    def _update_details(self, tonie: CreativeTonie) -> None:
        """Update details panel for selected tonie.

        Args:
            tonie: Selected Creative Tonie.
        """
        title = self.query_one("#details-title", Static)
        title.update(f'Kapitel für "{tonie.name}":')

        chapter_list = self.query_one("#chapter-list", ChapterList)
        chapter_list.update_chapters(tonie.chapters)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle household selection change."""
        if event.select.id == "household-select" and event.value:
            app: TonieApp = self.app  # type: ignore[assignment]
            app.state.current_household_id = str(event.value)
            app.state.save_preferences()
            self._load_tonies()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "refresh-button":
            self.action_refresh()
        elif event.button.id == "shuffle-button":
            self.action_shuffle()
        elif event.button.id == "clear-button":
            self.action_clear()
        elif event.button.id == "upload-button":
            self.action_upload()

    def action_refresh(self) -> None:
        """Refresh tonies list."""
        self._load_tonies()

    def action_shuffle(self) -> None:
        """Shuffle selected tonie chapters."""
        if not self._selected_tonie:
            self.notify("Bitte zuerst einen Tonie auswählen", severity="warning")
            return

        if len(self._selected_tonie.chapters) < 2:  # noqa: PLR2004
            self.notify("Mindestens 2 Kapitel zum Mischen erforderlich", severity="warning")
            return

        self._do_shuffle(self._selected_tonie)

    def action_clear(self) -> None:
        """Clear selected tonie chapters."""
        if not self._selected_tonie:
            self.notify("Bitte zuerst einen Tonie auswählen", severity="warning")
            return

        if not self._selected_tonie.chapters:
            self.notify("Keine Kapitel zum Löschen vorhanden", severity="warning")
            return

        # Show confirmation dialog
        def handle_confirm(confirmed: bool | None) -> None:
            if confirmed and self._selected_tonie:
                self._do_clear(self._selected_tonie)

        self.app.push_screen(
            ConfirmModal(
                f'{len(self._selected_tonie.chapters)} Kapitel von "{self._selected_tonie.name}" löschen?',
                title="Kapitel löschen",
            ),
            handle_confirm,
        )

    def action_upload(self) -> None:
        """Navigate to upload screen."""
        # Signal to dashboard to switch to upload view
        from tonie_api.tui.widgets.sidebar import Sidebar
        self.app.query_one(Sidebar).set_active("upload")
        self.app.query_one(Sidebar).post_message(Sidebar.Navigate("upload"))

    @work(exclusive=True, thread=True)
    def _load_tonies(self) -> None:
        """Load tonies in background."""
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
                ErrorModal(f"Fehler beim Laden: {e}"),
            )

    def _on_tonies_loaded(self, tonies: list[CreativeTonie]) -> None:
        """Handle loaded tonies.

        Args:
            tonies: List of loaded tonies.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.tonies = tonies
        self._populate_table()
        self._selected_tonie = None
        self.query_one("#details-title", Static).update("Wähle einen Tonie aus der Liste")
        self.query_one("#chapter-list", ChapterList).update_chapters([])
        self.notify("Tonies aktualisiert")

    @work(exclusive=True, thread=True)
    def _do_shuffle(self, tonie: CreativeTonie) -> None:
        """Shuffle tonie chapters in background.

        Args:
            tonie: Tonie to shuffle.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api or not app.state.current_household_id:
            return

        try:
            updated = app.state.api.shuffle_chapters(
                app.state.current_household_id,
                tonie.id,
            )
            app.call_from_thread(self._on_action_complete, updated, "gemischt")
        except AuthenticationError:
            app.call_from_thread(self._handle_auth_error)
        except TonieAPIError as e:
            app.call_from_thread(
                self.app.push_screen,
                ErrorModal(f"Fehler beim Mischen: {e}"),
            )

    @work(exclusive=True, thread=True)
    def _do_clear(self, tonie: CreativeTonie) -> None:
        """Clear tonie chapters in background.

        Args:
            tonie: Tonie to clear.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api or not app.state.current_household_id:
            return

        try:
            updated = app.state.api.clear_chapters(
                app.state.current_household_id,
                tonie.id,
            )
            app.call_from_thread(self._on_action_complete, updated, "gelöscht")
        except AuthenticationError:
            app.call_from_thread(self._handle_auth_error)
        except TonieAPIError as e:
            app.call_from_thread(
                self.app.push_screen,
                ErrorModal(f"Fehler beim Löschen: {e}"),
            )

    def _on_action_complete(self, tonie: CreativeTonie, action: str) -> None:
        """Handle completed action.

        Args:
            tonie: Updated tonie.
            action: Action description for notification.
        """
        # Update in tonies list
        app: TonieApp = self.app  # type: ignore[assignment]
        for i, t in enumerate(app.state.tonies):
            if t.id == tonie.id:
                app.state.tonies[i] = tonie
                break

        self._populate_table()
        self._selected_tonie = tonie
        self._update_details(tonie)
        self.notify(f'Kapitel von "{tonie.name}" {action}')

    def _handle_auth_error(self) -> None:
        """Handle authentication error by returning to login."""
        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.reset()
        app.switch_screen("login")
        app.push_screen(ErrorModal("Session abgelaufen. Bitte erneut anmelden."))

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds to mm:ss format.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted duration string.
        """
        minutes = int(seconds) // 60
        return f"{minutes}m"
