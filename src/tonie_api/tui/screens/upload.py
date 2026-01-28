"""Upload screen for uploading audio files to Creative Tonies."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DirectoryTree,
    ListItem,
    ListView,
    ProgressBar,
    Select,
    Static,
)

from tonie_api.exceptions import AuthenticationError, TonieAPIError
from tonie_api.tui.widgets.error_modal import ErrorModal

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.binding import BindingType

    from tonie_api.tui.app import TonieApp

logger = logging.getLogger(__name__)

# Supported audio file extensions
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".m4b", ".aac", ".ogg", ".wav", ".flac"}


class FilteredDirectoryTree(DirectoryTree):
    """Directory tree that filters for audio files."""

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """Filter paths to show only directories and audio files.

        Args:
            paths: List of paths to filter.

        Returns:
            Filtered list of paths.
        """
        return [
            path
            for path in paths
            if path.is_dir() or path.suffix.lower() in AUDIO_EXTENSIONS
        ]


class UploadScreen(Screen):
    """Screen for uploading audio files to Creative Tonies.

    Provides file browser, file selection, and upload progress.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("u", "upload", "Hochladen"),
        ("c", "clear_selection", "Auswahl leeren"),
        ("escape", "cancel", "Abbrechen"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize upload screen."""
        super().__init__(name=name, id=id, classes=classes)
        self._selected_files: list[Path] = []
        self._is_uploading = False
        self._current_file_index = 0

    def compose(self) -> ComposeResult:
        """Compose the upload screen."""
        app: TonieApp = self.app  # type: ignore[assignment]

        with Vertical():
            # Header with tonie selector
            with Horizontal(id="upload-header"):
                options = [
                    (f"{t.name} ({t.chapters_remaining} frei)", t.id)
                    for t in app.state.tonies
                ]
                yield Select(
                    options,
                    prompt="Tonie wählen...",
                    id="upload-tonie-select",
                )

            # File browser and selected files
            with Horizontal(id="upload-content"):
                with Container(id="file-browser"):
                    yield Static("Dateien:", classes="section-title")
                    yield FilteredDirectoryTree(
                        Path.home(),
                        id="directory-tree",
                    )

                with Container(id="selected-files"):
                    yield Static("Ausgewählt:", id="selected-files-title")
                    yield ListView(id="selected-list")
                    yield Static("", id="selected-summary")

            # Progress section
            with Container(id="upload-progress"):
                yield ProgressBar(id="progress-bar", show_eta=False)
                yield Static("", id="progress-text")

            # Action buttons
            with Horizontal(id="upload-actions"):
                yield Button("[U]pload", id="upload-button", variant="primary")
                yield Button("[C]lear", id="clear-button", variant="default")

    def on_directory_tree_file_selected(
        self,
        event: DirectoryTree.FileSelected,
    ) -> None:
        """Handle file selection from directory tree."""
        path = event.path
        if path.suffix.lower() not in AUDIO_EXTENSIONS:
            return

        if path in self._selected_files:
            # Remove if already selected
            self._selected_files.remove(path)
        else:
            # Add to selection
            self._selected_files.append(path)

        self._update_selected_list()

    def _update_selected_list(self) -> None:
        """Update the selected files list view."""
        list_view = self.query_one("#selected-list", ListView)
        list_view.clear()

        for path in self._selected_files:
            size_mb = path.stat().st_size / (1024 * 1024)
            list_view.append(
                ListItem(
                    Static(f"{path.name} ({size_mb:.1f} MB)"),
                    id=f"file-{hash(path)}",
                ),
            )

        # Update summary
        total_size = sum(p.stat().st_size for p in self._selected_files)
        total_mb = total_size / (1024 * 1024)
        summary = self.query_one("#selected-summary", Static)
        summary.update(f"Gesamt: {len(self._selected_files)} Dateien, {total_mb:.1f} MB")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "upload-button":
            self.action_upload()
        elif event.button.id == "clear-button":
            self.action_clear_selection()

    def action_upload(self) -> None:
        """Start upload process."""
        if self._is_uploading:
            return

        if not self._selected_files:
            self.notify("Keine Dateien ausgewählt", severity="warning")
            return

        tonie_select = self.query_one("#upload-tonie-select", Select)
        if not tonie_select.value:
            self.notify("Bitte zuerst einen Tonie auswählen", severity="warning")
            return

        self._is_uploading = True
        self._current_file_index = 0
        self._disable_controls(disabled=True)

        self._upload_files(str(tonie_select.value))

    def action_clear_selection(self) -> None:
        """Clear file selection."""
        if self._is_uploading:
            return

        self._selected_files.clear()
        self._update_selected_list()

    def action_cancel(self) -> None:
        """Cancel current operation."""
        if self._is_uploading:
            self.notify(
                "Upload kann nicht abgebrochen werden. Bitte warten...",
                severity="warning",
            )

    def _disable_controls(self, *, disabled: bool) -> None:
        """Enable/disable controls during upload.

        Args:
            disabled: Whether to disable controls.
        """
        self.query_one("#upload-button", Button).disabled = disabled
        self.query_one("#clear-button", Button).disabled = disabled
        self.query_one("#upload-tonie-select", Select).disabled = disabled
        self.query_one("#directory-tree", FilteredDirectoryTree).disabled = disabled

    @work(exclusive=True, thread=True)
    def _upload_files(self, tonie_id: str) -> None:
        """Upload files in background.

        Args:
            tonie_id: Target tonie ID.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api or not app.state.current_household_id:
            return

        total_files = len(self._selected_files)
        uploaded_count = 0
        failed_files: list[str] = []

        for i, file_path in enumerate(self._selected_files):
            self._current_file_index = i
            app.call_from_thread(
                self._update_progress,
                i,
                total_files,
                file_path.name,
            )

            try:
                # Request upload URL
                upload_request = app.state.api.request_file_upload()

                # Upload to S3 with progress - capture loop variables
                def make_progress_callback(
                    idx: int,
                    fname: str,
                ) -> callable:
                    def progress_callback(bytes_sent: int, total_bytes: int) -> None:
                        progress = (idx + (bytes_sent / total_bytes)) / total_files
                        app.call_from_thread(
                            self._update_file_progress,
                            progress,
                            fname,
                            bytes_sent,
                            total_bytes,
                        )

                    return progress_callback

                app.state.api.upload_to_s3(
                    file_path,
                    upload_request,
                    progress_callback=make_progress_callback(i, file_path.name),
                )

                # Add chapter
                app.state.api.add_chapter(
                    app.state.current_household_id,
                    tonie_id,
                    file_path.stem,
                    upload_request.file_id,
                )
                uploaded_count += 1

            except AuthenticationError:
                app.call_from_thread(self._handle_auth_error)
                return
            except TonieAPIError as e:
                logger.warning("Upload failed for %s: %s", file_path.name, e)
                failed_files.append(file_path.name)

        app.call_from_thread(
            self._upload_complete,
            uploaded_count,
            failed_files,
            tonie_id,
        )

    def _update_progress(self, current: int, total: int, filename: str) -> None:
        """Update progress display.

        Args:
            current: Current file index.
            total: Total number of files.
            filename: Current filename.
        """
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(total=total, progress=current)

        progress_text = self.query_one("#progress-text", Static)
        progress_text.update(f"Lade hoch: {filename} ({current + 1}/{total})")

    def _update_file_progress(
        self,
        overall_progress: float,
        filename: str,
        bytes_sent: int,
        total_bytes: int,
    ) -> None:
        """Update file upload progress.

        Args:
            overall_progress: Overall progress (0-1).
            filename: Current filename.
            bytes_sent: Bytes uploaded.
            total_bytes: Total bytes.
        """
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        # Use percentage for smoother updates
        progress_bar.update(total=100, progress=int(overall_progress * 100))

        sent_mb = bytes_sent / (1024 * 1024)
        total_mb = total_bytes / (1024 * 1024)
        progress_text = self.query_one("#progress-text", Static)
        progress_text.update(f"{filename}: {sent_mb:.1f}/{total_mb:.1f} MB")

    def _upload_complete(
        self,
        uploaded_count: int,
        failed_files: list[str],
        _tonie_id: str,
    ) -> None:
        """Handle upload completion.

        Args:
            uploaded_count: Number of successfully uploaded files.
            failed_files: List of failed filenames.
            tonie_id: Target tonie ID.
        """
        self._is_uploading = False
        self._disable_controls(disabled=False)

        # Reset progress
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(total=100, progress=100)

        progress_text = self.query_one("#progress-text", Static)

        if failed_files:
            progress_text.update(
                f"Fertig: {uploaded_count} hochgeladen, {len(failed_files)} fehlgeschlagen",
            )
            self.app.push_screen(
                ErrorModal(
                    "Folgende Dateien konnten nicht hochgeladen werden:\n"
                    + "\n".join(failed_files),
                    title="Upload teilweise fehlgeschlagen",
                ),
            )
        else:
            progress_text.update(f"Fertig: {uploaded_count} Dateien hochgeladen")
            self.notify(f"{uploaded_count} Dateien erfolgreich hochgeladen")

        # Clear selection
        self._selected_files.clear()
        self._update_selected_list()

        # Refresh tonies to update chapter counts
        self._refresh_tonies()

    @work(thread=True)
    def _refresh_tonies(self) -> None:
        """Refresh tonies list after upload."""
        app: TonieApp = self.app  # type: ignore[assignment]
        if not app.state.api or not app.state.current_household_id:
            return

        try:
            tonies = app.state.api.get_creative_tonies(app.state.current_household_id)
            app.call_from_thread(self._on_tonies_refreshed, tonies)
        except TonieAPIError:
            pass  # Ignore refresh errors

    def _on_tonies_refreshed(self, tonies: list) -> None:
        """Handle refreshed tonies data.

        Args:
            tonies: Updated tonies list.
        """
        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.tonies = tonies

        # Update tonie selector
        tonie_select = self.query_one("#upload-tonie-select", Select)
        options = [
            (f"{t.name} ({t.chapters_remaining} frei)", t.id)
            for t in tonies
        ]
        tonie_select.set_options(options)

    def _handle_auth_error(self) -> None:
        """Handle authentication error."""
        self._is_uploading = False
        self._disable_controls(disabled=False)

        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.reset()
        app.switch_screen("login")
        app.push_screen(ErrorModal("Session abgelaufen. Bitte erneut anmelden."))
