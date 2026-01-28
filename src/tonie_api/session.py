"""Session handling for the Tonie Cloud API with OAuth2 authentication."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class TonieCloudSession(requests.Session):
    """HTTP Session with OAuth2 token handling for the Tonie Cloud API."""

    TOKEN_URL = "https://login.tonies.com/auth/realms/tonies/protocol/openid-connect/token"  # noqa: S105
    CLIENT_ID = "my-tonies"
    BASE_URL = "https://api.tonie.cloud/v2"

    # Token will be refreshed this many seconds before expiry
    TOKEN_EXPIRY_BUFFER = 60

    def __init__(self, username: str, password: str):
        """Initialize session and acquire OAuth2 token.

        Args:
            username: Tonie Cloud username (email).
            password: Tonie Cloud password.

        Raises:
            requests.HTTPError: If authentication fails.
        """
        super().__init__()
        self._username = username
        self._password = password
        self._token_expires_at: float | None = None
        self._refresh_token: str | None = None

        # Configure retry strategy for transient errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("https://", adapter)
        self.mount("http://", adapter)

        self.acquire_token()

    def acquire_token(self) -> None:
        """Acquire OAuth2 access token via password grant.

        Raises:
            requests.HTTPError: If token request fails.
        """
        logger.debug("Acquiring new access token")
        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": self.CLIENT_ID,
                "scope": "openid",
                "username": self._username,
                "password": self._password,
            },
            timeout=30,
        )
        response.raise_for_status()
        self._handle_token_response(response.json())

    def _handle_token_response(self, token_data: dict) -> None:
        """Process and store token response data.

        Args:
            token_data: JSON response from token endpoint.
        """
        access_token = token_data["access_token"]
        self.headers.update({"Authorization": f"Bearer {access_token}"})

        # Store refresh token if available
        self._refresh_token = token_data.get("refresh_token")

        # Calculate token expiry time
        expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
        self._token_expires_at = time.time() + expires_in
        logger.debug("Token acquired, expires in %ds", expires_in)

    def _refresh_with_token(self) -> bool:
        """Attempt to refresh access token using refresh token.

        Returns:
            True if refresh was successful, False otherwise.
        """
        if not self._refresh_token:
            return False

        logger.debug("Refreshing access token")
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.CLIENT_ID,
                    "refresh_token": self._refresh_token,
                },
                timeout=30,
            )
            response.raise_for_status()
        except requests.HTTPError:
            logger.debug("Token refresh failed, will re-authenticate")
            self._refresh_token = None
            return False
        else:
            self._handle_token_response(response.json())
            return True

    def ensure_token_valid(self) -> None:
        """Ensure access token is valid, refreshing if necessary."""
        if self._token_expires_at is None:
            return

        if time.time() >= self._token_expires_at - self.TOKEN_EXPIRY_BUFFER:
            logger.debug("Token expired or expiring soon, refreshing")
            if not self._refresh_with_token():
                # Fallback to re-authentication with credentials
                self.acquire_token()

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Make an HTTP request, ensuring token validity.

        Args:
            method: HTTP method.
            url: Request URL.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response object.
        """
        self.ensure_token_valid()
        return super().request(method, url, **kwargs)
