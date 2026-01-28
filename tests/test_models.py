"""Tests for Pydantic models."""

from datetime import datetime, timezone

from tonie_api.models import (
    Chapter,
    Config,
    CreativeTonie,
    FileUploadRequest,
    Household,
    UploadRequestDetails,
    User,
)


class TestUser:
    def test_parse(self):
        data = {"uuid": "abc-123", "email": "test@example.com"}
        user = User.model_validate(data)
        assert user.uuid == "abc-123"
        assert user.email == "test@example.com"


class TestConfig:
    def test_parse_with_aliases(self):
        data = {
            "locales": ["de", "en"],
            "unicodeLocales": ["de-DE", "en-US"],
            "maxChapters": 99,
            "maxSeconds": 5400,
            "maxBytes": 536870912,
            "accepts": ["audio/mpeg", "audio/ogg"],
            "stageWarning": False,
            "paypalClientId": "paypal-id",
            "ssoEnabled": True,
        }
        config = Config.model_validate(data)
        assert config.locales == ["de", "en"]
        assert config.unicode_locales == ["de-DE", "en-US"]
        assert config.max_chapters == 99
        assert config.max_seconds == 5400
        assert config.max_bytes == 536870912
        assert config.accepts == ["audio/mpeg", "audio/ogg"]
        assert config.stage_warning is False
        assert config.paypal_client_id == "paypal-id"
        assert config.sso_enabled is True

    def test_parse_with_snake_case(self):
        data = {
            "locales": ["de"],
            "unicode_locales": ["de-DE"],
            "max_chapters": 99,
            "max_seconds": 5400,
            "max_bytes": 536870912,
            "accepts": ["audio/mpeg"],
            "stage_warning": False,
            "paypal_client_id": "paypal-id",
            "sso_enabled": True,
        }
        config = Config.model_validate(data)
        assert config.unicode_locales == ["de-DE"]
        assert config.max_chapters == 99


class TestHousehold:
    def test_parse_with_aliases(self):
        data = {
            "id": "household-123",
            "name": "My Home",
            "ownerName": "John Doe",
            "access": "owner",
            "canLeave": False,
        }
        household = Household.model_validate(data)
        assert household.id == "household-123"
        assert household.name == "My Home"
        assert household.owner_name == "John Doe"
        assert household.access == "owner"
        assert household.can_leave is False


class TestChapter:
    def test_parse(self):
        data = {
            "id": "chapter-1",
            "title": "Track 1",
            "file": "uuid-abc",
            "seconds": 123.45,
            "transcoding": False,
        }
        chapter = Chapter.model_validate(data)
        assert chapter.id == "chapter-1"
        assert chapter.title == "Track 1"
        assert chapter.file == "uuid-abc"
        assert chapter.seconds == 123.45
        assert chapter.transcoding is False


class TestCreativeTonie:
    def test_parse_with_chapters(self):
        data = {
            "id": "tonie-123",
            "householdId": "household-456",
            "name": "My Tonie",
            "imageUrl": "https://example.com/image.png",
            "secondsRemaining": 4800.5,
            "secondsPresent": 599.5,
            "chaptersRemaining": 90,
            "chaptersPresent": 9,
            "transcoding": False,
            "lastUpdate": "2024-01-15T10:30:00Z",
            "chapters": [
                {
                    "id": "ch-1",
                    "title": "Track 1",
                    "file": "file-1",
                    "seconds": 180.0,
                    "transcoding": False,
                }
            ],
        }
        tonie = CreativeTonie.model_validate(data)
        assert tonie.id == "tonie-123"
        assert tonie.household_id == "household-456"
        assert tonie.name == "My Tonie"
        assert tonie.image_url == "https://example.com/image.png"
        assert tonie.seconds_remaining == 4800.5
        assert tonie.seconds_present == 599.5
        assert tonie.chapters_remaining == 90
        assert tonie.chapters_present == 9
        assert tonie.transcoding is False
        assert tonie.last_update == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert len(tonie.chapters) == 1
        assert tonie.chapters[0].title == "Track 1"

    def test_parse_with_null_last_update(self):
        data = {
            "id": "tonie-123",
            "householdId": "household-456",
            "name": "New Tonie",
            "imageUrl": "https://example.com/image.png",
            "secondsRemaining": 5400.0,
            "secondsPresent": 0.0,
            "chaptersRemaining": 99,
            "chaptersPresent": 0,
            "transcoding": False,
            "lastUpdate": None,
            "chapters": [],
        }
        tonie = CreativeTonie.model_validate(data)
        assert tonie.last_update is None
        assert tonie.chapters == []


class TestUploadRequestDetails:
    def test_parse(self):
        data = {
            "url": "https://s3.amazonaws.com/bucket",
            "fields": {"key": "uploads/file.mp3", "policy": "abc123"},
        }
        details = UploadRequestDetails.model_validate(data)
        assert details.url == "https://s3.amazonaws.com/bucket"
        assert details.fields["key"] == "uploads/file.mp3"


class TestFileUploadRequest:
    def test_parse_with_alias(self):
        data = {
            "request": {
                "url": "https://s3.amazonaws.com/bucket",
                "fields": {"key": "uploads/file.mp3"},
            },
            "fileId": "file-uuid-123",
        }
        upload = FileUploadRequest.model_validate(data)
        assert upload.file_id == "file-uuid-123"
        assert upload.request.url == "https://s3.amazonaws.com/bucket"
        assert upload.request.fields["key"] == "uploads/file.mp3"
