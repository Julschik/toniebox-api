"""Login screen for the Tonie Cloud TUI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from tonie_api import TonieAPI
from tonie_api.exceptions import AuthenticationError, TonieAPIError

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.binding import BindingType

    from tonie_api.tui.app import TonieApp

logger = logging.getLogger(__name__)


class LoginScreen(Screen):
    """Login screen for Tonie Cloud authentication.

    Handles username/password input and validation.
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "quit", "Beenden"),
        ("enter", "submit", "Anmelden"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize login screen."""
        super().__init__(name=name, id=id, classes=classes)
        self._error_message: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the login screen."""
        with Container(id="login-container"):
            yield Static("Tonie Cloud Login", id="login-title")
            yield Static("", id="login-error")
            yield Static("E-Mail:", classes="login-label")
            yield Input(placeholder="email@example.com", id="login-input-email")
            yield Static("Passwort:", classes="login-label")
            yield Input(placeholder="********", password=True, id="login-input-password")
            yield Button("Anmelden", id="login-button", variant="primary")
            yield Static("Tab: Weiter | Enter: Anmelden | Esc: Beenden", id="login-footer")

    def on_mount(self) -> None:
        """Focus email input on mount."""
        self.query_one("#login-input-email", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in input fields."""
        if event.input.id == "login-input-email":
            # Move to password field
            self.query_one("#login-input-password", Input).focus()
        elif event.input.id == "login-input-password":
            # Submit login
            self._attempt_login()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle login button press."""
        if event.button.id == "login-button":
            self._attempt_login()

    def action_submit(self) -> None:
        """Handle enter key binding."""
        self._attempt_login()

    def action_quit(self) -> None:
        """Handle escape key to quit."""
        self.app.exit()

    def _attempt_login(self) -> None:
        """Start login attempt."""
        email_input = self.query_one("#login-input-email", Input)
        password_input = self.query_one("#login-input-password", Input)

        email = email_input.value.strip()
        password = password_input.value

        if not email or not password:
            self._show_error("Bitte E-Mail und Passwort eingeben.")
            return

        # Disable inputs during login
        email_input.disabled = True
        password_input.disabled = True
        self.query_one("#login-button", Button).disabled = True

        self._do_login(email, password)

    @work(exclusive=True, thread=True)
    def _do_login(self, email: str, password: str) -> None:
        """Perform login in background thread.

        Args:
            email: User email.
            password: User password.
        """
        try:
            api = TonieAPI(username=email, password=password)
            user = api.get_me()

            # Schedule UI update on main thread
            self.app.call_from_thread(self._login_success, api, user)

        except AuthenticationError:
            self.app.call_from_thread(
                self._login_failed,
                "Ungültige Zugangsdaten. Bitte E-Mail und Passwort überprüfen.",
            )
        except TonieAPIError as e:
            self.app.call_from_thread(
                self._login_failed,
                f"Verbindungsfehler: {e}",
            )

    def _login_success(self, api: TonieAPI, user: object) -> None:
        """Handle successful login.

        Args:
            api: Authenticated API instance.
            user: User object.
        """
        # Update app state
        app: TonieApp = self.app  # type: ignore[assignment]
        app.state.api = api
        app.state.user = user  # type: ignore[assignment]
        app.state.is_authenticated = True

        logger.info("Login successful: %s", getattr(user, "email", "unknown"))

        # Navigate to dashboard
        app.push_screen("dashboard")

    def _login_failed(self, message: str) -> None:
        """Handle failed login.

        Args:
            message: Error message to display.
        """
        self._show_error(message)

        # Re-enable inputs
        self.query_one("#login-input-email", Input).disabled = False
        password_input = self.query_one("#login-input-password", Input)
        password_input.disabled = False
        password_input.value = ""  # Clear password
        password_input.focus()
        self.query_one("#login-button", Button).disabled = False

    def _show_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message to show.
        """
        error_static = self.query_one("#login-error", Static)
        error_static.update(message)
