"""Tests for the TonieAPI class."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import responses

from tonie_api import (
    AuthenticationError,
    FileUploadRequest,
    NotFoundError,
    RateLimitError,
    ServerError,
    TonieAPI,
    TonieAPIError,
    ValidationError,
)
from tonie_api.session import TonieCloudSession


# Test fixtures
@pytest.fixture
def mock_session():
    """Create a mock session that doesn't require authentication."""
    session = MagicMock(spec=TonieCloudSession)
    session.headers = {"Authorization": "Bearer test-token"}
    return session


@pytest.fixture
def api(mock_session):
    """Create a TonieAPI instance with a mock session."""
    return TonieAPI(session=mock_session)


@pytest.fixture
def sample_user():
    return {"uuid": "user-123", "email": "test@example.com"}


@pytest.fixture
def sample_config():
    return {
        "locales": ["de", "en"],
        "unicodeLocales": ["de-DE", "en-US"],
        "maxChapters": 99,
        "maxSeconds": 5400,
        "maxBytes": 536870912,
        "accepts": ["audio/mpeg"],
        "stageWarning": False,
        "paypalClientId": "paypal-123",
        "ssoEnabled": True,
    }


@pytest.fixture
def sample_household():
    return {
        "id": "hh-123",
        "name": "My Home",
        "ownerName": "John Doe",
        "access": "owner",
        "canLeave": False,
    }


@pytest.fixture
def sample_tonie():
    return {
        "id": "tonie-123",
        "householdId": "hh-123",
        "name": "My Tonie",
        "imageUrl": "https://example.com/image.png",
        "secondsRemaining": 5000.0,
        "secondsPresent": 400.0,
        "chaptersRemaining": 97,
        "chaptersPresent": 2,
        "transcoding": False,
        "lastUpdate": "2024-01-15T10:30:00Z",
        "chapters": [
            {"id": "ch-1", "title": "Track 1", "file": "file-1", "seconds": 200.0, "transcoding": False},
            {"id": "ch-2", "title": "Track 2", "file": "file-2", "seconds": 200.0, "transcoding": False},
        ],
    }


@pytest.fixture
def sample_upload_request():
    return {
        "request": {
            "url": "https://s3.amazonaws.com/tonie-bucket",
            "fields": {
                "key": "uploads/abc123.mp3",
                "policy": "encoded-policy",
                "x-amz-credential": "credential",
                "x-amz-signature": "signature",
            },
        },
        "fileId": "file-uuid-123",
    }


BASE_URL = TonieCloudSession.BASE_URL


class TestTonieAPIInitialization:
    """Tests for TonieAPI initialization."""

    @responses.activate
    def test_init_with_credentials(self):
        """Test initialization with explicit credentials."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token", "token_type": "Bearer"},
            status=200,
        )

        api = TonieAPI(username="test@example.com", password="secret")
        assert api._session is not None

    @responses.activate
    def test_init_with_env_credentials(self):
        """Test initialization with credentials from environment."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"access_token": "test-token", "token_type": "Bearer"},
            status=200,
        )

        with patch.dict("os.environ", {"USERNAME": "env@example.com", "PASSWORD": "env-secret"}):
            api = TonieAPI()
            assert api._session is not None

    def test_init_without_credentials(self):
        """Test that initialization fails without credentials."""
        # Need to explicitly clear USERNAME and PASSWORD
        with patch.dict("os.environ", {"USERNAME": "", "PASSWORD": ""}, clear=False), pytest.raises(
            AuthenticationError, match="Username and password are required"
        ):
            TonieAPI()

    @responses.activate
    def test_init_with_invalid_credentials(self):
        """Test that invalid credentials raise AuthenticationError."""
        responses.add(
            responses.POST,
            TonieCloudSession.TOKEN_URL,
            json={"error": "invalid_grant"},
            status=401,
        )

        with pytest.raises(AuthenticationError, match="Authentication failed"):
            TonieAPI(username="bad@example.com", password="wrong")

    def test_init_with_session(self, mock_session):
        """Test initialization with pre-configured session."""
        api = TonieAPI(session=mock_session)
        assert api._session is mock_session


class TestCoreAPIMethods:
    """Tests for core API methods."""

    @responses.activate
    def test_get_me(self, api, mock_session, sample_user):
        """Test fetching current user."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_user)

        user = api.get_me()
        assert user.uuid == "user-123"
        assert user.email == "test@example.com"
        mock_session.request.assert_called_once_with("GET", f"{BASE_URL}/me")

    def test_get_config(self, api, mock_session, sample_config):
        """Test fetching configuration."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_config)

        config = api.get_config()
        assert config.max_chapters == 99
        assert config.max_seconds == 5400
        mock_session.request.assert_called_once_with("GET", f"{BASE_URL}/config")

    def test_get_households(self, api, mock_session, sample_household):
        """Test fetching households."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: [sample_household])

        households = api.get_households()
        assert len(households) == 1
        assert households[0].id == "hh-123"
        assert households[0].name == "My Home"

    def test_get_creative_tonies(self, api, mock_session, sample_tonie):
        """Test fetching creative tonies for a household."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: [sample_tonie])

        tonies = api.get_creative_tonies("hh-123")
        assert len(tonies) == 1
        assert tonies[0].id == "tonie-123"
        assert tonies[0].name == "My Tonie"
        mock_session.request.assert_called_once_with("GET", f"{BASE_URL}/households/hh-123/creativetonies")

    def test_get_creative_tonie(self, api, mock_session, sample_tonie):
        """Test fetching a specific creative tonie."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_tonie)

        tonie = api.get_creative_tonie("hh-123", "tonie-123")
        assert tonie.id == "tonie-123"
        assert len(tonie.chapters) == 2
        mock_session.request.assert_called_once_with(
            "GET", f"{BASE_URL}/households/hh-123/creativetonies/tonie-123"
        )

    def test_update_creative_tonie_chapters(self, api, mock_session, sample_tonie):
        """Test updating creative tonie chapters."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_tonie)

        chapters = [{"id": "ch-1", "title": "Track 1", "file": "file-1"}]
        tonie = api.update_creative_tonie("hh-123", "tonie-123", chapters=chapters)
        assert tonie.id == "tonie-123"
        mock_session.request.assert_called_once_with(
            "PATCH",
            f"{BASE_URL}/households/hh-123/creativetonies/tonie-123",
            json={"chapters": chapters},
        )

    def test_update_creative_tonie_name(self, api, mock_session, sample_tonie):
        """Test updating creative tonie name."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_tonie)

        tonie = api.update_creative_tonie("hh-123", "tonie-123", name="New Name")
        assert tonie.id == "tonie-123"
        mock_session.request.assert_called_once_with(
            "PATCH",
            f"{BASE_URL}/households/hh-123/creativetonies/tonie-123",
            json={"name": "New Name"},
        )

    def test_add_chapter(self, api, mock_session, sample_tonie):
        """Test adding a chapter to a tonie."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_tonie)

        tonie = api.add_chapter("hh-123", "tonie-123", "New Track", "file-uuid")
        assert tonie.id == "tonie-123"
        mock_session.request.assert_called_once_with(
            "POST",
            f"{BASE_URL}/households/hh-123/creativetonies/tonie-123/chapters",
            json={"title": "New Track", "file": "file-uuid"},
        )

    def test_request_file_upload(self, api, mock_session, sample_upload_request):
        """Test requesting a file upload URL."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_upload_request)

        upload = api.request_file_upload()
        assert upload.file_id == "file-uuid-123"
        assert upload.request.url == "https://s3.amazonaws.com/tonie-bucket"
        mock_session.request.assert_called_once_with("POST", f"{BASE_URL}/file")


class TestErrorHandling:
    """Tests for error handling."""

    def test_handle_401_error(self, api, mock_session):
        """Test that 401 raises AuthenticationError."""
        mock_response = MagicMock(
            ok=False, status_code=401, text="Unauthorized", json=lambda: {"message": "Invalid token"}
        )
        mock_session.request.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            api.get_me()
        assert exc_info.value.status_code == 401

    def test_handle_403_error(self, api, mock_session):
        """Test that 403 raises AuthenticationError."""
        mock_response = MagicMock(
            ok=False, status_code=403, text="Forbidden", json=lambda: {"message": "Access denied"}
        )
        mock_session.request.return_value = mock_response

        with pytest.raises(AuthenticationError) as exc_info:
            api.get_me()
        assert exc_info.value.status_code == 403

    def test_handle_404_error(self, api, mock_session):
        """Test that 404 raises NotFoundError."""
        mock_response = MagicMock(
            ok=False, status_code=404, text="Not Found", json=lambda: {"message": "Resource not found"}
        )
        mock_session.request.return_value = mock_response

        with pytest.raises(NotFoundError) as exc_info:
            api.get_creative_tonie("hh-123", "nonexistent")
        assert exc_info.value.status_code == 404

    def test_handle_429_error(self, api, mock_session):
        """Test that 429 raises RateLimitError."""
        mock_response = MagicMock(
            ok=False, status_code=429, text="Too Many Requests", json=lambda: {"message": "Rate limit exceeded"}
        )
        mock_session.request.return_value = mock_response

        with pytest.raises(RateLimitError) as exc_info:
            api.get_me()
        assert exc_info.value.status_code == 429

    def test_handle_400_error(self, api, mock_session):
        """Test that 400 raises ValidationError."""
        mock_response = MagicMock(
            ok=False, status_code=400, text="Bad Request", json=lambda: {"message": "Invalid data"}
        )
        mock_session.request.return_value = mock_response

        with pytest.raises(ValidationError) as exc_info:
            api.update_creative_tonie("hh-123", "tonie-123", chapters=[])
        assert exc_info.value.status_code == 400

    def test_handle_500_error(self, api, mock_session):
        """Test that 500 raises ServerError."""
        mock_response = MagicMock(
            ok=False, status_code=500, text="Internal Server Error", json=lambda: {"message": "Server error"}
        )
        mock_session.request.return_value = mock_response

        with pytest.raises(ServerError) as exc_info:
            api.get_me()
        assert exc_info.value.status_code == 500

    def test_handle_502_error(self, api, mock_session):
        """Test that 502 raises ServerError."""
        mock_response = MagicMock(
            ok=False, status_code=502, text="Bad Gateway", json=lambda: {"message": "Bad gateway"}
        )
        mock_session.request.return_value = mock_response

        with pytest.raises(ServerError) as exc_info:
            api.get_me()
        assert exc_info.value.status_code == 502

    def test_handle_unknown_error(self, api, mock_session):
        """Test that unknown errors raise TonieAPIError."""
        mock_response = MagicMock(
            ok=False, status_code=418, text="I'm a teapot", json=lambda: {"message": "Teapot"}
        )
        mock_session.request.return_value = mock_response

        with pytest.raises(TonieAPIError) as exc_info:
            api.get_me()
        assert exc_info.value.status_code == 418

    def test_handle_error_without_json(self, api, mock_session):
        """Test error handling when response has no JSON."""
        mock_response = MagicMock(ok=False, status_code=500, text="Internal Error")
        mock_response.json.side_effect = ValueError("No JSON")
        mock_session.request.return_value = mock_response

        with pytest.raises(ServerError) as exc_info:
            api.get_me()
        assert exc_info.value.message == "Internal Error"


class TestConvenienceMethods:
    """Tests for convenience methods."""

    @responses.activate
    def test_upload_to_s3(self, api, mock_session, sample_upload_request):
        """Test uploading a file to S3."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_upload_request)

        # Mock S3 upload
        responses.add(
            responses.POST,
            "https://s3.amazonaws.com/tonie-bucket",
            status=204,
        )

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio data")
            temp_path = f.name

        try:
            file_id = api.upload_to_s3(temp_path)
            assert file_id == "file-uuid-123"
        finally:
            Path(temp_path).unlink()

    @responses.activate
    def test_upload_to_s3_with_request(self, api, sample_upload_request):
        """Test uploading with a pre-fetched upload request."""
        upload_request = FileUploadRequest.model_validate(sample_upload_request)

        responses.add(
            responses.POST,
            "https://s3.amazonaws.com/tonie-bucket",
            status=204,
        )

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio data")
            temp_path = f.name

        try:
            file_id = api.upload_to_s3(temp_path, upload_request=upload_request)
            assert file_id == "file-uuid-123"
        finally:
            Path(temp_path).unlink()

    @responses.activate
    def test_upload_audio_file(self, api, mock_session, sample_upload_request, sample_tonie):
        """Test the complete upload flow."""
        # Mock request_file_upload
        mock_session.request.side_effect = [
            MagicMock(ok=True, json=lambda: sample_upload_request),  # POST /file
            MagicMock(ok=True, json=lambda: sample_tonie),  # POST chapters
        ]

        # Mock S3 upload
        responses.add(
            responses.POST,
            "https://s3.amazonaws.com/tonie-bucket",
            status=204,
        )

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio data")
            temp_path = f.name

        try:
            tonie = api.upload_audio_file(temp_path, "hh-123", "tonie-123", title="My Track")
            assert tonie.id == "tonie-123"

            # Verify add_chapter was called with correct args
            calls = mock_session.request.call_args_list
            assert len(calls) == 2
            # Second call should be add_chapter
            assert calls[1][0][0] == "POST"
            assert "chapters" in calls[1][0][1]
        finally:
            Path(temp_path).unlink()

    @responses.activate
    def test_upload_audio_file_default_title(self, api, mock_session, sample_upload_request, sample_tonie):
        """Test upload with default title from filename."""
        mock_session.request.side_effect = [
            MagicMock(ok=True, json=lambda: sample_upload_request),
            MagicMock(ok=True, json=lambda: sample_tonie),
        ]

        responses.add(
            responses.POST,
            "https://s3.amazonaws.com/tonie-bucket",
            status=204,
        )

        with tempfile.NamedTemporaryFile(suffix=".mp3", prefix="my_song_", delete=False) as f:
            f.write(b"fake audio data")
            temp_path = f.name

        try:
            api.upload_audio_file(temp_path, "hh-123", "tonie-123")
            # Title should be extracted from filename
            calls = mock_session.request.call_args_list
            add_chapter_call = calls[1]
            # Verify title is the filename stem
            assert Path(temp_path).stem in str(add_chapter_call)
        finally:
            Path(temp_path).unlink()

    def test_shuffle_chapters(self, api, mock_session, sample_tonie):
        """Test shuffling chapters."""
        # First call: get_creative_tonie
        # Second call: update_creative_tonie
        mock_session.request.side_effect = [
            MagicMock(ok=True, json=lambda: sample_tonie),
            MagicMock(ok=True, json=lambda: sample_tonie),
        ]

        with patch("random.shuffle") as mock_shuffle:
            tonie = api.shuffle_chapters("hh-123", "tonie-123")
            assert tonie.id == "tonie-123"
            mock_shuffle.assert_called_once()

    def test_shuffle_chapters_single_chapter(self, api, mock_session):
        """Test that shuffling with single chapter returns unchanged."""
        single_chapter_tonie = {
            "id": "tonie-123",
            "householdId": "hh-123",
            "name": "My Tonie",
            "imageUrl": "https://example.com/image.png",
            "secondsRemaining": 5200.0,
            "secondsPresent": 200.0,
            "chaptersRemaining": 98,
            "chaptersPresent": 1,
            "transcoding": False,
            "lastUpdate": None,
            "chapters": [{"id": "ch-1", "title": "Track 1", "file": "file-1", "seconds": 200.0, "transcoding": False}],
        }
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: single_chapter_tonie)

        tonie = api.shuffle_chapters("hh-123", "tonie-123")
        assert tonie.id == "tonie-123"
        # Should only call get, not update
        assert mock_session.request.call_count == 1

    def test_shuffle_chapters_empty(self, api, mock_session):
        """Test that shuffling with no chapters returns unchanged."""
        empty_tonie = {
            "id": "tonie-123",
            "householdId": "hh-123",
            "name": "My Tonie",
            "imageUrl": "https://example.com/image.png",
            "secondsRemaining": 5400.0,
            "secondsPresent": 0.0,
            "chaptersRemaining": 99,
            "chaptersPresent": 0,
            "transcoding": False,
            "lastUpdate": None,
            "chapters": [],
        }
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: empty_tonie)

        tonie = api.shuffle_chapters("hh-123", "tonie-123")
        assert tonie.chapters == []
        assert mock_session.request.call_count == 1

    def test_clear_chapters(self, api, mock_session, sample_tonie):
        """Test clearing all chapters."""
        cleared_tonie = sample_tonie.copy()
        cleared_tonie["chapters"] = []
        cleared_tonie["chaptersPresent"] = 0
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: cleared_tonie)

        tonie = api.clear_chapters("hh-123", "tonie-123")
        assert tonie.chapters == []
        mock_session.request.assert_called_once_with(
            "PATCH",
            f"{BASE_URL}/households/hh-123/creativetonies/tonie-123",
            json={"chapters": []},
        )

    def test_set_chapters(self, api, mock_session, sample_tonie):
        """Test setting chapters to a specific list."""
        mock_session.request.return_value = MagicMock(ok=True, json=lambda: sample_tonie)

        chapters = [
            {"id": "ch-2", "title": "Track 2", "file": "file-2"},
            {"id": "ch-1", "title": "Track 1", "file": "file-1"},
        ]
        tonie = api.set_chapters("hh-123", "tonie-123", chapters)
        assert tonie.id == "tonie-123"
        mock_session.request.assert_called_once_with(
            "PATCH",
            f"{BASE_URL}/households/hh-123/creativetonies/tonie-123",
            json={"chapters": chapters},
        )


class TestExceptionAttributes:
    """Tests for exception attributes."""

    def test_tonie_api_error_attributes(self):
        """Test TonieAPIError stores all attributes."""
        mock_response = MagicMock()
        error = TonieAPIError("Test error", status_code=500, response=mock_response)
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.response is mock_response
        assert str(error) == "Test error"

    def test_authentication_error_inherits(self):
        """Test AuthenticationError inherits from TonieAPIError."""
        error = AuthenticationError("Auth failed", status_code=401)
        assert isinstance(error, TonieAPIError)
        assert error.status_code == 401

    def test_not_found_error_inherits(self):
        """Test NotFoundError inherits from TonieAPIError."""
        error = NotFoundError("Not found", status_code=404)
        assert isinstance(error, TonieAPIError)

    def test_rate_limit_error_inherits(self):
        """Test RateLimitError inherits from TonieAPIError."""
        error = RateLimitError("Rate limited", status_code=429)
        assert isinstance(error, TonieAPIError)

    def test_validation_error_inherits(self):
        """Test ValidationError inherits from TonieAPIError."""
        error = ValidationError("Invalid", status_code=400)
        assert isinstance(error, TonieAPIError)

    def test_server_error_inherits(self):
        """Test ServerError inherits from TonieAPIError."""
        error = ServerError("Server error", status_code=500)
        assert isinstance(error, TonieAPIError)
