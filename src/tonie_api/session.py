"""Session handling for the Tonie Cloud API with OAuth2 authentication."""

import requests


class TonieCloudSession(requests.Session):
    """HTTP Session with OAuth2 token handling for the Tonie Cloud API."""

    TOKEN_URL = "https://login.tonies.com/auth/realms/tonies/protocol/openid-connect/token"  # noqa: S105
    CLIENT_ID = "my-tonies"
    BASE_URL = "https://api.tonie.cloud/v2"

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
        self.acquire_token()

    def acquire_token(self) -> None:
        """Acquire OAuth2 access token via password grant.

        Raises:
            requests.HTTPError: If token request fails.
        """
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
        token_data = response.json()
        access_token = token_data["access_token"]
        self.headers.update({"Authorization": f"Bearer {access_token}"})
