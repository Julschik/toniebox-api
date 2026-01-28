"""Error modal dialog for the Tonie Cloud TUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.binding import BindingType


class ErrorModal(ModalScreen[None]):
    """Modal dialog for displaying error messages.

    Args:
        message: Error message to display.
        title: Optional title for the dialog.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "dismiss", "Close"),
        ("enter", "dismiss", "Close"),
    ]

    def __init__(
        self,
        message: str,
        title: str = "Fehler",
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize error modal.

        Args:
            message: Error message to display.
            title: Dialog title.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._message = message
        self._title = title

    def compose(self) -> ComposeResult:
        """Compose the error dialog."""
        with Container(id="error-dialog"):
            yield Static(self._title, id="error-title")
            yield Static(self._message, id="error-message")
            yield Button("OK", id="error-button", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "error-button":
            self.dismiss()


class ConfirmModal(ModalScreen[bool]):
    """Modal dialog for confirmation prompts.

    Args:
        message: Confirmation message to display.
        title: Optional title for the dialog.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "cancel", "Cancel"),
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
    ]

    def __init__(
        self,
        message: str,
        title: str = "Bestätigen",
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize confirm modal.

        Args:
            message: Confirmation message.
            title: Dialog title.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._message = message
        self._title = title

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Container(id="confirm-dialog"):
            yield Static(self._title, id="confirm-title")
            yield Static(self._message, id="confirm-message")
            with Container(id="confirm-buttons"):
                yield Button("Ja", id="confirm-yes", variant="warning")
                yield Button("Nein", id="confirm-no", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "confirm-yes":
            self.dismiss(True)  # noqa: FBT003
        elif event.button.id == "confirm-no":
            self.dismiss(False)  # noqa: FBT003

    def action_confirm(self) -> None:
        """Confirm action."""
        self.dismiss(True)  # noqa: FBT003

    def action_cancel(self) -> None:
        """Cancel action."""
        self.dismiss(False)  # noqa: FBT003
