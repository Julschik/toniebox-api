"""Sidebar navigation widget for the Tonie Cloud TUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from textual.containers import Container
from textual.message import Message
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult


@dataclass
class NavItem:
    """Navigation item configuration."""

    id: str
    label: str
    key: str
    is_danger: bool = False


class Sidebar(Container):
    """Sidebar navigation widget.

    Provides navigation between different views in the dashboard.
    """

    NAV_ITEMS: ClassVar[list[NavItem]] = [
        NavItem("home", "Home", "1"),
        NavItem("tonies", "Tonies", "2"),
        NavItem("upload", "Upload", "3"),
        NavItem("presets", "Presets", "4"),
        NavItem("settings", "Einstellungen", "5"),
    ]

    @dataclass
    class Navigate(Message):
        """Posted when user selects a navigation item."""

        view_id: str

    @dataclass
    class Logout(Message):
        """Posted when user clicks logout."""

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize sidebar.

        Args:
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._active_id = "home"

    def compose(self) -> ComposeResult:
        """Compose the sidebar."""
        yield Static("Navigation", classes="sidebar-title")

        for item in self.NAV_ITEMS:
            classes = "nav-item"
            if item.id == self._active_id:
                classes += " -active"
            yield Button(
                f"[{item.key}] {item.label}",
                id=f"nav-{item.id}",
                classes=classes,
            )

        # Spacer
        yield Static("", classes="sidebar-spacer")

        # Logout button
        yield Button(
            "[Q] Logout",
            id="nav-logout",
            classes="nav-item -danger",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button press."""
        button_id = event.button.id
        if button_id is None:
            return

        if button_id == "nav-logout":
            self.post_message(self.Logout())
            return

        if button_id.startswith("nav-"):
            view_id = button_id[4:]  # Remove "nav-" prefix
            self._set_active(view_id)
            self.post_message(self.Navigate(view_id))

    def _set_active(self, view_id: str) -> None:
        """Update active navigation item.

        Args:
            view_id: ID of the view to activate.
        """
        self._active_id = view_id

        # Update button classes
        for item in self.NAV_ITEMS:
            button = self.query_one(f"#nav-{item.id}", Button)
            if item.id == view_id:
                button.add_class("-active")
            else:
                button.remove_class("-active")

    def set_active(self, view_id: str) -> None:
        """Externally set active navigation item.

        Args:
            view_id: ID of the view to activate.
        """
        self._set_active(view_id)
