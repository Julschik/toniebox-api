"""Main API client for the Tonie Cloud API."""

from __future__ import annotations

import logging
import os
import random
from http import HTTPStatus
from pathlib import Path
from typing import Any, Protocol

import requests
from dotenv import load_dotenv

from tonie_api.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TonieAPIError,
    ValidationError,
)
from tonie_api.models import (
    Config,
    CreativeTonie,
    FileUploadRequest,
    Household,
    User,
)
from tonie_api.session import TonieCloudSession

logger = logging.getLogger(__name__)


class ProgressCallback(Protocol):
    """Protocol for upload progress callbacks."""

    def __call__(self, bytes_sent: int, total_bytes: int) -> None:
        """Called during upload with progress information.

        Args:
            bytes_sent: Number of bytes uploaded so far.
            total_bytes: Total number of bytes to upload.
        """
        ...

_MIN_SHUFFLE_CHAPTERS = 2


class _ProgressFileWrapper:
    """File wrapper that tracks read progress for upload callbacks."""

    def __init__(
        self,
        file_obj: Any,
        total_size: int,
        callback: ProgressCallback,
    ) -> None:
        """Initialize wrapper.

        Args:
            file_obj: File object to wrap.
            total_size: Total file size in bytes.
            callback: Progress callback function.
        """
        self._file = file_obj
        self._total_size = total_size
        self._callback = callback
        self._bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        """Read from file and report progress."""
        data = self._file.read(size)
        self._bytes_read += len(data)
        self._callback(self._bytes_read, self._total_size)
        return data

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek in file."""
        return self._file.seek(offset, whence)

    def tell(self) -> int:
        """Return current position."""
        return self._file.tell()


class TonieAPI:
    """Client for the Tonie Cloud API.

    Provides methods to interact with the Tonie Cloud API including
    authentication, retrieving data, and managing Creative Tonies.
    """

    DEFAULT_TIMEOUT = 30
    """Default timeout for API requests in seconds."""

    UPLOAD_TIMEOUT = 300
    """Timeout for S3 upload requests in seconds."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        *,
        session: TonieCloudSession | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize the Tonie API client.

        Credentials can be provided directly or loaded from environment
        variables (TONIE_USERNAME, TONIE_PASSWORD) via a .env file.

        Args:
            username: Tonie Cloud username (email). Falls back to TONIE_USERNAME env var.
            password: Tonie Cloud password. Falls back to TONIE_PASSWORD env var.
            session: Optional pre-configured session. If provided, username/password
                are ignored.
            timeout: Request timeout in seconds. Defaults to DEFAULT_TIMEOUT.

        Raises:
            AuthenticationError: If credentials are missing or invalid.
        """
        self._timeout = timeout or self.DEFAULT_TIMEOUT

        if session is not None:
            self._session = session
        else:
            # Load from global config first, then local .env, then env vars
            config_file = Path.home() / ".config" / "tonie-api" / "credentials"
            if config_file.exists():
                load_dotenv(config_file)
            load_dotenv()  # Also load local .env (overrides global)
            username = username or os.environ.get("TONIE_USERNAME")
            password = password or os.environ.get("TONIE_PASSWORD")

            if not username or not password:
                msg = "Username and password are required"
                raise AuthenticationError(msg)

            try:
                self._session = TonieCloudSession(username, password)
            except requests.HTTPError as e:
                msg = "Authentication failed"
                raise AuthenticationError(msg, status_code=e.response.status_code, response=e.response) from e

        logger.debug("TonieAPI initialized successfully")

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Make an authenticated request to the API.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.).
            path: API path (without base URL).
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response object.

        Raises:
            TonieAPIError: On API errors.
        """
        url = f"{TonieCloudSession.BASE_URL}{path}"
        logger.debug("%s %s", method, url)

        # Apply default timeout if not specified
        if "timeout" not in kwargs:
            kwargs["timeout"] = self._timeout

        response = self._session.request(method, url, **kwargs)

        if not response.ok:
            self._handle_error_response(response)

        return response

    def _handle_error_response(self, response: requests.Response) -> None:
        """Convert HTTP error response to appropriate exception.

        Args:
            response: The error response.

        Raises:
            AuthenticationError: For 401/403 responses.
            NotFoundError: For 404 responses.
            RateLimitError: For 429 responses.
            ValidationError: For 400 responses.
            ServerError: For 5xx responses.
            TonieAPIError: For other error responses.
        """
        status = response.status_code
        try:
            detail = response.json()
            message = detail.get("message", response.text)
        except (ValueError, KeyError):
            message = response.text or f"HTTP {status}"

        if status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            raise AuthenticationError(message, status_code=status, response=response)
        if status == HTTPStatus.NOT_FOUND:
            raise NotFoundError(message, status_code=status, response=response)
        if status == HTTPStatus.TOO_MANY_REQUESTS:
            raise RateLimitError(message, status_code=status, response=response)
        if status == HTTPStatus.BAD_REQUEST:
            raise ValidationError(message, status_code=status, response=response)
        if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            raise ServerError(message, status_code=status, response=response)
        raise TonieAPIError(message, status_code=status, response=response)

    # Core API Methods

    def get_me(self) -> User:
        """Get current user information.

        Returns:
            User object with uuid and email.
        """
        response = self._request("GET", "/me")
        return User.model_validate(response.json())

    def get_config(self) -> Config:
        """Get backend configuration.

        Returns:
            Config object with limits and settings.
        """
        response = self._request("GET", "/config")
        return Config.model_validate(response.json())

    def get_households(self) -> list[Household]:
        """Get all households for the current user.

        Returns:
            List of Household objects.
        """
        response = self._request("GET", "/households")
        return [Household.model_validate(h) for h in response.json()]

    def get_creative_tonies(self, household_id: str) -> list[CreativeTonie]:
        """Get all Creative Tonies in a household.

        Args:
            household_id: The household ID.

        Returns:
            List of CreativeTonie objects.
        """
        response = self._request("GET", f"/households/{household_id}/creativetonies")
        return [CreativeTonie.model_validate(t) for t in response.json()]

    def get_creative_tonie(self, household_id: str, tonie_id: str) -> CreativeTonie:
        """Get a specific Creative Tonie.

        Args:
            household_id: The household ID.
            tonie_id: The Creative Tonie ID.

        Returns:
            CreativeTonie object.
        """
        response = self._request("GET", f"/households/{household_id}/creativetonies/{tonie_id}")
        return CreativeTonie.model_validate(response.json())

    def update_creative_tonie(
        self,
        household_id: str,
        tonie_id: str,
        *,
        chapters: list[dict[str, str]] | None = None,
        name: str | None = None,
    ) -> CreativeTonie:
        """Update a Creative Tonie.

        Args:
            household_id: The household ID.
            tonie_id: The Creative Tonie ID.
            chapters: Optional list of chapter dicts with 'id', 'title', 'file' keys.
            name: Optional new name for the Tonie.

        Returns:
            Updated CreativeTonie object.
        """
        data: dict[str, Any] = {}
        if chapters is not None:
            data["chapters"] = chapters
        if name is not None:
            data["name"] = name

        response = self._request("PATCH", f"/households/{household_id}/creativetonies/{tonie_id}", json=data)
        return CreativeTonie.model_validate(response.json())

    def add_chapter(
        self,
        household_id: str,
        tonie_id: str,
        title: str,
        file_id: str,
    ) -> CreativeTonie:
        """Add a chapter to a Creative Tonie.

        Args:
            household_id: The household ID.
            tonie_id: The Creative Tonie ID.
            title: Chapter title.
            file_id: File ID from upload or content token.

        Returns:
            Updated CreativeTonie object.
        """
        data = {"title": title, "file": file_id}
        response = self._request("POST", f"/households/{household_id}/creativetonies/{tonie_id}/chapters", json=data)
        return CreativeTonie.model_validate(response.json())

    def request_file_upload(self) -> FileUploadRequest:
        """Request a presigned URL for file upload.

        Returns:
            FileUploadRequest with S3 upload details and file ID.
        """
        response = self._request("POST", "/file")
        return FileUploadRequest.model_validate(response.json())

    # Convenience Methods

    def upload_to_s3(
        self,
        file_path: str | Path,
        upload_request: FileUploadRequest | None = None,
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> str:
        """Upload a file to S3 using presigned URL.

        Args:
            file_path: Path to the audio file.
            upload_request: Optional pre-fetched upload request.
                If not provided, a new one will be requested.
            progress_callback: Optional callback for upload progress.
                Called with (bytes_sent, total_bytes) during upload.

        Returns:
            The file ID for use in add_chapter.

        Raises:
            ValidationError: If file does not exist or is not a file.
            ServerError: If S3 upload fails.
            TonieAPIError: If upload times out.
        """
        if upload_request is None:
            upload_request = self.request_file_upload()

        file_path = Path(file_path)

        if not file_path.exists():
            msg = f"Datei nicht gefunden: {file_path}"
            raise ValidationError(msg)
        if not file_path.is_file():
            msg = f"Kein gültiger Dateipfad: {file_path}"
            raise ValidationError(msg)

        file_size = file_path.stat().st_size
        logger.debug("Uploading %s (%d bytes) to S3", file_path.name, file_size)

        try:
            with file_path.open("rb") as f:
                # Wrap file with progress tracking if callback provided
                file_obj = _ProgressFileWrapper(f, file_size, progress_callback) if progress_callback else f

                files = {"file": (upload_request.request.fields["key"], file_obj)}
                response = requests.post(
                    upload_request.request.url,
                    data=upload_request.request.fields,
                    files=files,
                    timeout=self.UPLOAD_TIMEOUT,
                )
                response.raise_for_status()
        except requests.HTTPError as e:
            msg = f"S3 Upload fehlgeschlagen: {e.response.status_code}"
            raise ServerError(msg, status_code=e.response.status_code, response=e.response) from e
        except requests.Timeout as e:
            msg = "S3 Upload Timeout"
            raise TonieAPIError(msg) from e
        except requests.RequestException as e:
            msg = f"S3 Upload Verbindungsfehler: {e}"
            raise TonieAPIError(msg) from e

        logger.debug("Upload complete, file_id=%s", upload_request.file_id)
        return upload_request.file_id

    def upload_audio_file(
        self,
        file_path: str | Path,
        household_id: str,
        tonie_id: str,
        title: str | None = None,
    ) -> CreativeTonie:
        """Upload an audio file and add it as a chapter to a Creative Tonie.

        This is a convenience method that performs the complete upload flow:
        1. Request upload URL
        2. Upload to S3
        3. Add chapter to Tonie

        Args:
            file_path: Path to the audio file.
            household_id: The household ID.
            tonie_id: The Creative Tonie ID.
            title: Optional chapter title. Defaults to filename without extension.

        Returns:
            Updated CreativeTonie object.
        """
        file_path = Path(file_path)
        if title is None:
            title = file_path.stem

        file_id = self.upload_to_s3(file_path)
        return self.add_chapter(household_id, tonie_id, title, file_id)

    def shuffle_chapters(self, household_id: str, tonie_id: str) -> CreativeTonie:
        """Shuffle the chapters of a Creative Tonie.

        Uses Fisher-Yates shuffle algorithm.

        Args:
            household_id: The household ID.
            tonie_id: The Creative Tonie ID.

        Returns:
            Updated CreativeTonie object with shuffled chapters.
        """
        tonie = self.get_creative_tonie(household_id, tonie_id)

        if len(tonie.chapters) < _MIN_SHUFFLE_CHAPTERS:
            return tonie

        chapters = [{"id": c.id, "title": c.title, "file": c.file} for c in tonie.chapters]
        random.shuffle(chapters)

        return self.update_creative_tonie(household_id, tonie_id, chapters=chapters)

    def clear_chapters(self, household_id: str, tonie_id: str) -> CreativeTonie:
        """Remove all chapters from a Creative Tonie.

        Args:
            household_id: The household ID.
            tonie_id: The Creative Tonie ID.

        Returns:
            Updated CreativeTonie object with no chapters.
        """
        return self.update_creative_tonie(household_id, tonie_id, chapters=[])

    def set_chapters(
        self,
        household_id: str,
        tonie_id: str,
        chapters: list[dict[str, str]],
    ) -> CreativeTonie:
        """Set the chapters of a Creative Tonie.

        Args:
            household_id: The household ID.
            tonie_id: The Creative Tonie ID.
            chapters: List of chapter dicts with 'id', 'title', 'file' keys.

        Returns:
            Updated CreativeTonie object.
        """
        return self.update_creative_tonie(household_id, tonie_id, chapters=chapters)
