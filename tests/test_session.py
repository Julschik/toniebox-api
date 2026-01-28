"""Tests for the TonieCloudSession class."""

import time
from unittest.mock import patch

import pytest
import responses
from requests.exceptions import ConnectionError as RequestsConnectionError

from tonie_api.session import TonieCloudSession


class TestAcquireToken:
    """Tests for token acquisition."""

    @responses.activate
    def test_acquire_token_success(self):
        """Test successful token acquisition."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={
                "access_token": "test-access-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "test-refresh-token",
            },
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password123")

        assert session.headers["Authorization"] == "Bearer test-access-token"

    @responses.activate
    def test_acquire_token_invalid_credentials(self):
        """Test that invalid credentials raise HTTPError."""
        import requests

        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"error": "invalid_grant", "error_description": "Invalid credentials"},
            status=401,
        )

        with pytest.raises(requests.HTTPError):
            TonieCloudSession("bad@example.com", "wrongpassword")

    @responses.activate
    def test_acquire_token_network_error(self):
        """Test that network errors are propagated."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            body=RequestsConnectionError("Connection refused"),
        )

        with pytest.raises(RequestsConnectionError):
            TonieCloudSession("user@example.com", "password")

    @responses.activate
    def test_acquire_token_stores_credentials(self):
        """Test that credentials are stored for potential re-auth."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token", "token_type": "Bearer"},
            status=200,
        )

        session = TonieCloudSession("stored@example.com", "storedpass")

        assert session._username == "stored@example.com"
        assert session._password == "storedpass"

    @responses.activate
    def test_acquire_token_minimal_response(self):
        """Test token acquisition with minimal response (no expires_in/refresh_token)."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "minimal-token"},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        assert session.headers["Authorization"] == "Bearer minimal-token"


class TestSessionConfiguration:
    """Tests for session configuration and constants."""

    def test_token_url_is_https(self):
        """Verify TOKEN_URL uses HTTPS."""
        assert TonieCloudSession.TOKEN_URL.startswith("https://")

    def test_base_url_is_https(self):
        """Verify BASE_URL uses HTTPS."""
        assert TonieCloudSession.BASE_URL.startswith("https://")

    def test_client_id_is_set(self):
        """Verify CLIENT_ID is configured."""
        assert TonieCloudSession.CLIENT_ID == "my-tonies"

    def test_token_url_points_to_tonies(self):
        """Verify TOKEN_URL points to official Tonie endpoint."""
        assert "tonies.com" in TonieCloudSession.TOKEN_URL

    def test_base_url_points_to_tonies(self):
        """Verify BASE_URL points to official Tonie API."""
        assert "tonie.cloud" in TonieCloudSession.BASE_URL


class TestSessionInheritance:
    """Tests for session inheritance from requests.Session."""

    @responses.activate
    def test_inherits_from_requests_session(self):
        """Test that TonieCloudSession is a requests.Session."""
        import requests

        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token"},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        assert isinstance(session, requests.Session)

    @responses.activate
    def test_session_can_make_requests(self):
        """Test that session can make authenticated requests."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.tonie.cloud/v2/me",
            json={"uuid": "123", "email": "test@example.com"},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")
        response = session.get("https://api.tonie.cloud/v2/me")

        assert response.status_code == 200
        assert "Authorization" in responses.calls[1].request.headers


class TestTokenRequestPayload:
    """Tests for the OAuth token request payload."""

    @responses.activate
    def test_token_request_includes_grant_type(self):
        """Test that token request includes password grant type."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token"},
            status=200,
        )

        TonieCloudSession("user@example.com", "password")

        request_body = responses.calls[0].request.body
        assert "grant_type=password" in request_body

    @responses.activate
    def test_token_request_includes_client_id(self):
        """Test that token request includes client_id."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token"},
            status=200,
        )

        TonieCloudSession("user@example.com", "password")

        request_body = responses.calls[0].request.body
        assert "client_id=my-tonies" in request_body

    @responses.activate
    def test_token_request_includes_scope(self):
        """Test that token request includes openid scope."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token"},
            status=200,
        )

        TonieCloudSession("user@example.com", "password")

        request_body = responses.calls[0].request.body
        assert "scope=openid" in request_body

    @responses.activate
    def test_token_request_includes_credentials(self):
        """Test that token request includes username and password."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token"},
            status=200,
        )

        TonieCloudSession("test@example.com", "secret123")

        request_body = responses.calls[0].request.body
        assert "username=test%40example.com" in request_body  # URL encoded @
        assert "password=secret123" in request_body


class TestTokenRefresh:
    """Tests for token refresh functionality."""

    @responses.activate
    def test_acquire_token_stores_expiry(self):
        """Test that token expiry time is stored."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token", "expires_in": 3600},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        assert session._token_expires_at is not None
        assert session._token_expires_at > time.time()

    @responses.activate
    def test_acquire_token_stores_refresh_token(self):
        """Test that refresh token is stored when provided."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={
                "access_token": "test-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600,
            },
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        assert session._refresh_token == "test-refresh-token"

    @responses.activate
    def test_ensure_token_valid_no_refresh_needed(self):
        """Test that token is not refreshed when still valid."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token", "expires_in": 3600},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")
        original_token = session.headers["Authorization"]

        session.ensure_token_valid()

        # Token should not have changed
        assert session.headers["Authorization"] == original_token
        # Only one token request should have been made
        assert len(responses.calls) == 1

    @responses.activate
    def test_ensure_token_valid_refreshes_when_expired(self):
        """Test that token is refreshed when expired."""
        # Initial token acquisition
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={
                "access_token": "old-token",
                "refresh_token": "refresh-token",
                "expires_in": 3600,
            },
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        # Simulate expired token
        session._token_expires_at = time.time() - 1

        # Add response for refresh
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={
                "access_token": "new-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 3600,
            },
            status=200,
        )

        session.ensure_token_valid()

        assert session.headers["Authorization"] == "Bearer new-token"

    @responses.activate
    def test_ensure_token_valid_reauths_when_no_refresh_token(self):
        """Test that re-authentication occurs when no refresh token."""
        # Initial token without refresh token
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "old-token", "expires_in": 3600},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        # Simulate expired token
        session._token_expires_at = time.time() - 1

        # Add response for re-auth
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "reauth-token", "expires_in": 3600},
            status=200,
        )

        session.ensure_token_valid()

        assert session.headers["Authorization"] == "Bearer reauth-token"
        # Verify password grant was used (not refresh)
        request_body = responses.calls[1].request.body
        assert "grant_type=password" in request_body

    @responses.activate
    def test_refresh_token_failure_falls_back_to_reauth(self):
        """Test fallback to re-auth when refresh fails."""
        # Initial token with refresh token
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={
                "access_token": "old-token",
                "refresh_token": "invalid-refresh",
                "expires_in": 3600,
            },
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")
        session._token_expires_at = time.time() - 1

        # Refresh fails
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"error": "invalid_grant"},
            status=400,
        )

        # Re-auth succeeds
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "reauth-token", "expires_in": 3600},
            status=200,
        )

        session.ensure_token_valid()

        assert session.headers["Authorization"] == "Bearer reauth-token"
        # Refresh token should be cleared after failure
        assert session._refresh_token is None

    @responses.activate
    def test_request_method_ensures_token_valid(self):
        """Test that request method calls ensure_token_valid."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token", "expires_in": 3600},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://api.tonie.cloud/v2/test",
            json={"result": "ok"},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        with patch.object(session, "ensure_token_valid") as mock_ensure:
            session.request("GET", "https://api.tonie.cloud/v2/test")
            mock_ensure.assert_called_once()


class TestRetryConfiguration:
    """Tests for retry configuration."""

    @responses.activate
    def test_retry_adapter_is_configured(self):
        """Test that retry adapter is mounted."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token"},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        # Check that adapters are mounted
        assert "https://" in session.adapters
        assert "http://" in session.adapters

    @responses.activate
    def test_token_expiry_buffer(self):
        """Test that TOKEN_EXPIRY_BUFFER is reasonable."""
        assert TonieCloudSession.TOKEN_EXPIRY_BUFFER == 60  # 60 seconds

        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token", "expires_in": 100},
            status=200,
        )

        session = TonieCloudSession("user@example.com", "password")

        # Token should be considered expired 60s before actual expiry
        session._token_expires_at = time.time() + 30  # 30s left

        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "new-token", "expires_in": 3600},
            status=200,
        )

        session.ensure_token_valid()

        # Should have refreshed because we're within the buffer
        assert session.headers["Authorization"] == "Bearer new-token"
