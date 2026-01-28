"""Presets screen for managing automation presets."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from textual import work
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Static

from tonie_api.presets import (
    PresetError,
    delete_preset,
    load_presets,
    run_preset,
)
from tonie_api.tui.widgets.error_modal import ConfirmModal, ErrorModal

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.binding import BindingType

    from tonie_api.tui.app import TonieApp

logger = logging.getLogger(__name__)

_MAX_DESCRIPTION_LENGTH = 40


class PresetsScreen(Screen):
    """Screen for managing automation presets.

    Displays preset list and provides run/delete functionality.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("r", "run_preset", "Ausführen"),
        ("d", "delete_preset", "Löschen"),
        ("n", "new_preset", "Neu"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize presets screen."""
        super().__init__(name=name, id=id, classes=classes)
        self._selected_preset: str | None = None
        self._presets: dict[str, dict[str, Any]] = {}

    def compose(self) -> ComposeResult:
        """Compose the presets screen."""
        with Vertical():
            # Header
            with Horizontal(id="presets-header"):
                yield Static("Presets", classes="section-title")
                yield Button("Aktualisieren", id="refresh-presets-button", variant="default")

            # Presets table
            yield DataTable(id="presets-table")

            # Empty state
            yield Static(
                "Keine Presets vorhanden.\n"
                "Erstelle Presets mit: toniebox preset create <name>",
                id="presets-empty",
            )

            # Action buttons
            with Horizontal(id="presets-actions"):
                yield Button("[R]un", id="run-preset-button", variant="primary")
                yield Button("[D]elete", id="delete-preset-button", variant="warning")

    def on_mount(self) -> None:
        """Initialize table and load presets."""
        table = self.query_one("#presets-table", DataTable)
        table.add_column("Name", key="name")
        table.add_column("Beschreibung", key="description")
        table.add_column("Aktionen", key="actions")
        table.cursor_type = "row"

        self._load_presets()

    def _load_presets(self) -> None:
        """Load presets from configuration."""
        try:
            self._presets = load_presets()
        except PresetError as e:
            logger.warning("Failed to load presets: %s", e)
            self._presets = {}

        self._populate_table()

    def _populate_table(self) -> None:
        """Populate the presets table."""
        table = self.query_one("#presets-table", DataTable)
        empty_msg = self.query_one("#presets-empty", Static)

        table.clear()

        if not self._presets:
            table.display = False
            empty_msg.display = True
            return

        table.display = True
        empty_msg.display = False

        for name, preset in self._presets.items():
            description = preset.get("description", "-")
            actions_count = len(preset.get("actions", []))
            truncated_desc = (
                description[:_MAX_DESCRIPTION_LENGTH] + "..."
                if len(description) > _MAX_DESCRIPTION_LENGTH
                else description
            )
            table.add_row(name, truncated_desc, str(actions_count), key=name)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle preset selection."""
        self._selected_preset = event.row_key.value if event.row_key else None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "refresh-presets-button":
            self._load_presets()
        elif event.button.id == "run-preset-button":
            self.action_run_preset()
        elif event.button.id == "delete-preset-button":
            self.action_delete_preset()

    def action_run_preset(self) -> None:
        """Run selected preset."""
        if not self._selected_preset:
            self.notify("Bitte zuerst ein Preset auswählen", severity="warning")
            return

        self._run_preset(self._selected_preset)

    def action_delete_preset(self) -> None:
        """Delete selected preset."""
        if not self._selected_preset:
            self.notify("Bitte zuerst ein Preset auswählen", severity="warning")
            return

        preset = self._presets.get(self._selected_preset, {})
        actions_count = len(preset.get("actions", []))

        def handle_confirm(confirmed: bool | None) -> None:
            if confirmed and self._selected_preset:
                self._delete_preset(self._selected_preset)

        self.app.push_screen(
            ConfirmModal(
                f'Preset "{self._selected_preset}" mit {actions_count} Aktionen löschen?',
                title="Preset löschen",
            ),
            handle_confirm,
        )

    def action_new_preset(self) -> None:
        """Create new preset (redirect to CLI)."""
        self.notify(
            "Verwende 'toniebox preset create <name>' in der Kommandozeile",
            severity="information",
        )

    @work(exclusive=True, thread=True)
    def _run_preset(self, preset_name: str) -> None:
        """Run preset in background.

        Args:
            preset_name: Name of preset to run.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api:
            return

        app.call_from_thread(self.notify, f'Starte Preset "{preset_name}"...')

        try:
            results = run_preset(app.state.api, preset_name)
            app.call_from_thread(self._on_preset_complete, preset_name, results)
        except PresetError as e:
            app.call_from_thread(
                self.app.push_screen,
                ErrorModal(f"Preset-Fehler: {e}"),
            )

    def _on_preset_complete(
        self,
        preset_name: str,
        results: list[dict[str, Any]],
    ) -> None:
        """Handle preset completion.

        Args:
            preset_name: Name of completed preset.
            results: List of action results.
        """
        successful = sum(1 for r in results if r["status"] == "success")
        total = len(results)

        if successful == total:
            self.notify(f'Preset "{preset_name}": {successful}/{total} Aktionen erfolgreich')
        else:
            failed_actions = [
                f"{r['action']} auf {r['target']}: {r.get('error', 'unbekannt')}"
                for r in results
                if r["status"] != "success"
            ]
            self.app.push_screen(
                ErrorModal(
                    f'Preset "{preset_name}": {successful}/{total} erfolgreich\n\n'
                    "Fehlgeschlagen:\n" + "\n".join(failed_actions),
                    title="Preset teilweise fehlgeschlagen",
                ),
            )

        # Refresh tonies after preset run
        self._refresh_tonies()

    @work(thread=True)
    def _refresh_tonies(self) -> None:
        """Refresh tonies after preset run."""
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api or not app.state.current_household_id:
            return

        try:
            tonies = app.state.api.get_creative_tonies(app.state.current_household_id)
            app.call_from_thread(setattr, app.state, "tonies", tonies)
        except Exception:  # noqa: BLE001
            logger.debug("Failed to refresh tonies after preset run", exc_info=True)

    def _delete_preset(self, preset_name: str) -> None:
        """Delete preset.

        Args:
            preset_name: Name of preset to delete.
        """
        try:
            delete_preset(preset_name)
            self._selected_preset = None
            self._load_presets()
            self.notify(f'Preset "{preset_name}" gelöscht')
        except PresetError as e:
            self.app.push_screen(ErrorModal(str(e)))
