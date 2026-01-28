"""Tests for the CLI commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from tonie_api.cli.main import cli
from tonie_api.exceptions import AuthenticationError, TonieAPIError
from tonie_api.models import Chapter, CreativeTonie, FileUploadRequest, Household, UploadRequestDetails, User


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return User(uuid="user-123", email="test@example.com")


@pytest.fixture
def mock_households():
    """Create mock households."""
    return [
        Household(id="hh-1", name="My Home", ownerName="Test User", access="owner", canLeave=False),
        Household(id="hh-2", name="Other Home", ownerName="Other User", access="member", canLeave=True),
    ]


@pytest.fixture
def mock_creative_tonies():
    """Create mock creative tonies."""
    return [
        CreativeTonie(
            id="tonie-1",
            householdId="hh-1",
            name="Story Tonie",
            imageUrl="https://example.com/img1.png",
            secondsRemaining=3600.0,
            secondsPresent=120.0,
            chaptersRemaining=98,
            chaptersPresent=2,
            transcoding=False,
            chapters=[
                Chapter(id="ch-1", title="Chapter 1", file="file-1", seconds=60.0, transcoding=False),
                Chapter(id="ch-2", title="Chapter 2", file="file-2", seconds=60.0, transcoding=False),
            ],
        ),
        CreativeTonie(
            id="tonie-2",
            householdId="hh-1",
            name="Music Tonie",
            imageUrl="https://example.com/img2.png",
            secondsRemaining=7200.0,
            secondsPresent=0.0,
            chaptersRemaining=100,
            chaptersPresent=0,
            transcoding=False,
            chapters=[],
        ),
    ]


@pytest.fixture
def mock_upload_request():
    """Create a mock upload request."""
    return FileUploadRequest(
        request=UploadRequestDetails(
            url="https://s3.example.com/upload",
            fields={"key": "uploads/file-123.mp3", "policy": "xxx"},
        ),
        fileId="file-123",
    )


class TestHelpCommand:
    """Tests for help output."""

    def test_main_help(self, runner):
        """Test main help message."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Tonie Cloud CLI" in result.output
        assert "me" in result.output
        assert "households" in result.output
        assert "tonies" in result.output
        assert "upload" in result.output
        assert "shuffle" in result.output
        assert "clear" in result.output

    def test_me_help(self, runner):
        """Test me command help."""
        result = runner.invoke(cli, ["me", "--help"])
        assert result.exit_code == 0
        assert "user information" in result.output

    def test_households_help(self, runner):
        """Test households command help."""
        result = runner.invoke(cli, ["households", "--help"])
        assert result.exit_code == 0
        assert "List all households" in result.output

    def test_tonies_help(self, runner):
        """Test tonies command help."""
        result = runner.invoke(cli, ["tonies", "--help"])
        assert result.exit_code == 0
        assert "Creative Tonies" in result.output

    def test_upload_help(self, runner):
        """Test upload command help."""
        result = runner.invoke(cli, ["upload", "--help"])
        assert result.exit_code == 0
        assert "audio file" in result.output

    def test_shuffle_help(self, runner):
        """Test shuffle command help."""
        result = runner.invoke(cli, ["shuffle", "--help"])
        assert result.exit_code == 0
        assert "Shuffle chapters" in result.output

    def test_clear_help(self, runner):
        """Test clear command help."""
        result = runner.invoke(cli, ["clear", "--help"])
        assert result.exit_code == 0
        assert "Clear all chapters" in result.output


class TestMeCommand:
    """Tests for the me command."""

    def test_me_success(self, runner, mock_user):
        """Test successful me command."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_me.return_value = mock_user
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["me"])

            assert result.exit_code == 0
            assert "user-123" in result.output
            assert "test@example.com" in result.output

    def test_me_json_output(self, runner, mock_user):
        """Test me command with JSON output."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_me.return_value = mock_user
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["--json", "me"])

            assert result.exit_code == 0
            assert '"uuid": "user-123"' in result.output
            assert '"email": "test@example.com"' in result.output

    def test_me_authentication_error(self, runner):
        """Test me command with authentication error."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api_class.side_effect = AuthenticationError("Invalid credentials")

            result = runner.invoke(cli, ["me"])

            assert result.exit_code == 1
            assert "Invalid credentials" in result.output


class TestHouseholdsCommand:
    """Tests for the households command."""

    def test_households_success(self, runner, mock_households):
        """Test successful households command."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["households"])

            assert result.exit_code == 0
            assert "hh-1" in result.output
            assert "My Home" in result.output
            assert "hh-2" in result.output

    def test_households_json_output(self, runner, mock_households):
        """Test households command with JSON output."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["--json", "households"])

            assert result.exit_code == 0
            assert '"id": "hh-1"' in result.output
            assert '"name": "My Home"' in result.output

    def test_households_empty(self, runner):
        """Test households command with no households."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = []
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["households"])

            assert result.exit_code == 0
            assert "Keine Haushalte gefunden" in result.output or "No households found" in result.output


class TestToniesCommand:
    """Tests for the tonies command."""

    def test_tonies_with_household_id(self, runner, mock_creative_tonies):
        """Test tonies command with explicit household ID."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_creative_tonies.return_value = mock_creative_tonies
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["tonies", "hh-1"])

            assert result.exit_code == 0
            assert "tonie-1" in result.output
            assert "Story Tonie" in result.output
            mock_api.get_creative_tonies.assert_called_once_with("hh-1")

    def test_tonies_without_household_id(self, runner, mock_households, mock_creative_tonies):
        """Test tonies command using first household."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api.get_creative_tonies.return_value = mock_creative_tonies
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["tonies"])

            assert result.exit_code == 0
            mock_api.get_creative_tonies.assert_called_once_with("hh-1")

    def test_tonies_json_output(self, runner, mock_creative_tonies):
        """Test tonies command with JSON output."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_creative_tonies.return_value = mock_creative_tonies
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["--json", "tonies", "hh-1"])

            assert result.exit_code == 0
            assert '"id": "tonie-1"' in result.output

    def test_tonies_empty(self, runner):
        """Test tonies command with no tonies."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_creative_tonies.return_value = []
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["tonies", "hh-1"])

            assert result.exit_code == 0
            assert "Keine Creative Tonies" in result.output or "No Creative Tonies" in result.output


class TestUploadCommand:
    """Tests for the upload command."""

    def test_upload_success(self, runner, mock_households, mock_creative_tonies, mock_upload_request, tmp_path):
        """Test successful upload command."""
        # Create a test file
        test_file = tmp_path / "test_audio.mp3"
        test_file.write_bytes(b"fake audio content")

        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api.request_file_upload.return_value = mock_upload_request
            mock_api.upload_to_s3.return_value = "file-123"
            mock_api.add_chapter.return_value = mock_creative_tonies[0]
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["upload", str(test_file), "tonie-1"])

            assert result.exit_code == 0
            assert "test_audio" in result.output
            assert ("hochgeladen" in result.output or "Uploaded" in result.output)
            mock_api.add_chapter.assert_called_once()

    def test_upload_with_title(self, runner, mock_households, mock_creative_tonies, mock_upload_request, tmp_path):
        """Test upload command with custom title."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio content")

        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api.request_file_upload.return_value = mock_upload_request
            mock_api.upload_to_s3.return_value = "file-123"
            mock_api.add_chapter.return_value = mock_creative_tonies[0]
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["upload", str(test_file), "tonie-1", "--title", "Custom Title"])

            assert result.exit_code == 0
            mock_api.add_chapter.assert_called_once_with("hh-1", "tonie-1", "Custom Title", "file-123")

    def test_upload_with_household(self, runner, mock_creative_tonies, mock_upload_request, tmp_path):
        """Test upload command with explicit household."""
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(b"fake audio content")

        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.request_file_upload.return_value = mock_upload_request
            mock_api.upload_to_s3.return_value = "file-123"
            mock_api.add_chapter.return_value = mock_creative_tonies[0]
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["upload", str(test_file), "tonie-1", "--household", "hh-2"])

            assert result.exit_code == 0
            mock_api.add_chapter.assert_called_once_with("hh-2", "tonie-1", "test", "file-123")

    def test_upload_file_not_found(self, runner):
        """Test upload command with non-existent file."""
        result = runner.invoke(cli, ["upload", "/nonexistent/file.mp3", "tonie-1"])

        assert result.exit_code != 0
        assert "does not exist" in result.output or "Error" in result.output


class TestShuffleCommand:
    """Tests for the shuffle command."""

    def test_shuffle_success(self, runner, mock_households, mock_creative_tonies):
        """Test successful shuffle command."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api.shuffle_chapters.return_value = mock_creative_tonies[0]
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["shuffle", "tonie-1"])

            assert result.exit_code == 0
            assert "gemischt" in result.output or "Shuffled" in result.output
            mock_api.shuffle_chapters.assert_called_once_with("hh-1", "tonie-1")

    def test_shuffle_with_household(self, runner, mock_creative_tonies):
        """Test shuffle command with explicit household."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.shuffle_chapters.return_value = mock_creative_tonies[0]
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["shuffle", "tonie-1", "--household", "hh-2"])

            assert result.exit_code == 0
            mock_api.shuffle_chapters.assert_called_once_with("hh-2", "tonie-1")

    def test_shuffle_json_output(self, runner, mock_creative_tonies):
        """Test shuffle command with JSON output."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.shuffle_chapters.return_value = mock_creative_tonies[0]
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["--json", "shuffle", "tonie-1", "-h", "hh-1"])

            assert result.exit_code == 0
            assert '"id": "tonie-1"' in result.output


class TestClearCommand:
    """Tests for the clear command."""

    def test_clear_with_confirmation(self, runner, mock_households, mock_creative_tonies):
        """Test clear command with confirmation prompt."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api.get_creative_tonie.return_value = mock_creative_tonies[0]
            mock_api.clear_chapters.return_value = mock_creative_tonies[1]  # Empty tonie
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["clear", "tonie-1"], input="y\n")

            assert result.exit_code == 0
            assert "gelöscht" in result.output or "Cleared" in result.output
            mock_api.clear_chapters.assert_called_once()

    def test_clear_with_yes_flag(self, runner, mock_households, mock_creative_tonies):
        """Test clear command with --yes flag."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api.get_creative_tonie.return_value = mock_creative_tonies[0]
            mock_api.clear_chapters.return_value = mock_creative_tonies[1]
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["clear", "tonie-1", "--yes"])

            assert result.exit_code == 0
            assert "gelöscht" in result.output or "Cleared" in result.output

    def test_clear_aborted(self, runner, mock_households, mock_creative_tonies):
        """Test clear command when user declines."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api.get_creative_tonie.return_value = mock_creative_tonies[0]
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["clear", "tonie-1"], input="n\n")

            assert result.exit_code == 1
            assert "Aborted" in result.output
            mock_api.clear_chapters.assert_not_called()

    def test_clear_empty_tonie(self, runner, mock_households, mock_creative_tonies):
        """Test clear command on tonie with no chapters."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = mock_households
            mock_api.get_creative_tonie.return_value = mock_creative_tonies[1]  # Empty tonie
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["clear", "tonie-2"])

            assert result.exit_code == 0
            assert "keine Kapitel" in result.output or "no chapters" in result.output
            mock_api.clear_chapters.assert_not_called()


class TestErrorHandling:
    """Tests for error handling."""

    def test_api_error_handling(self, runner):
        """Test that API errors are handled gracefully."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.side_effect = TonieAPIError("Something went wrong")
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["households"])

            assert result.exit_code == 1
            assert "Something went wrong" in result.output

    def test_no_households_for_resolve(self, runner):
        """Test error when no households available for resolution."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_households.return_value = []
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["tonies"])

            assert result.exit_code == 1
            assert "Keine Haushalte" in result.output or "No households" in result.output


class TestConfigCommand:
    """Tests for the config command."""

    def test_config_success(self, runner):
        """Test successful config command."""
        from tonie_api.models import Config

        mock_config = Config(
            locales=["de", "en"],
            unicode_locales=["de-DE", "en-US"],
            max_chapters=99,
            max_seconds=5400,
            max_bytes=536870912,
            accepts=["audio/mpeg"],
            stage_warning=False,
            paypal_client_id="paypal-123",
            sso_enabled=True,
        )

        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_config.return_value = mock_config
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["config"])

            assert result.exit_code == 0
            assert "99" in result.output  # max_chapters
            assert "90" in result.output  # 5400 / 60 = 90 minutes
            assert "512" in result.output  # 536870912 / 1024 / 1024 = 512 MB
            assert "audio/mpeg" in result.output

    def test_config_json_output(self, runner):
        """Test config command with JSON output."""
        from tonie_api.models import Config

        mock_config = Config(
            locales=["de"],
            unicode_locales=["de-DE"],
            max_chapters=50,
            max_seconds=3600,
            max_bytes=268435456,
            accepts=["audio/mpeg"],
            stage_warning=False,
            paypal_client_id="test",
            sso_enabled=False,
        )

        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_config.return_value = mock_config
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["--json", "config"])

            assert result.exit_code == 0
            assert '"maxChapters": 50' in result.output


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_success(self, runner, mock_user):
        """Test successful status command."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_me.return_value = mock_user
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "erreichbar" in result.output

    def test_status_json_output(self, runner, mock_user):
        """Test status command with JSON output."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_me.return_value = mock_user
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["--json", "status"])

            assert result.exit_code == 0
            assert '"status": "ok"' in result.output
            assert '"latency_ms"' in result.output

    def test_status_api_unreachable(self, runner):
        """Test status command when API is unreachable."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_me.side_effect = TonieAPIError("Connection failed")
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 1
            assert "nicht erreichbar" in result.output


class TestLoginCommand:
    """Tests for the login command."""

    def test_login_success(self, runner, mock_user, tmp_path):
        """Test successful login command."""
        with (
            patch("tonie_api.cli.commands.TonieAPI") as mock_api_class,
            patch("tonie_api.cli.commands.CONFIG_DIR", tmp_path),
            patch("tonie_api.cli.commands.CREDENTIALS_FILE", tmp_path / "credentials"),
        ):
            mock_api = MagicMock()
            mock_api.get_me.return_value = mock_user
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["login"], input="test@example.com\nsecret\n")

            assert result.exit_code == 0
            assert "Eingeloggt" in result.output
            assert (tmp_path / "credentials").exists()

            # Verify credentials content
            content = (tmp_path / "credentials").read_text()
            assert "TONIE_USERNAME=test@example.com" in content
            assert "TONIE_PASSWORD=secret" in content

    def test_login_invalid_credentials(self, runner, tmp_path):
        """Test login command with invalid credentials."""
        with (
            patch("tonie_api.cli.commands.TonieAPI") as mock_api_class,
            patch("tonie_api.cli.commands.CONFIG_DIR", tmp_path),
            patch("tonie_api.cli.commands.CREDENTIALS_FILE", tmp_path / "credentials"),
        ):
            mock_api_class.side_effect = AuthenticationError("Invalid credentials")

            result = runner.invoke(cli, ["login"], input="bad@example.com\nwrong\n")

            assert result.exit_code == 1
            assert "Ungültige Zugangsdaten" in result.output
            assert not (tmp_path / "credentials").exists()

    def test_login_file_permissions(self, runner, mock_user, tmp_path):
        """Test that credentials file has correct permissions."""
        import stat

        with (
            patch("tonie_api.cli.commands.TonieAPI") as mock_api_class,
            patch("tonie_api.cli.commands.CONFIG_DIR", tmp_path),
            patch("tonie_api.cli.commands.CREDENTIALS_FILE", tmp_path / "credentials"),
        ):
            mock_api = MagicMock()
            mock_api.get_me.return_value = mock_user
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["login"], input="test@example.com\nsecret\n")

            assert result.exit_code == 0
            cred_file = tmp_path / "credentials"
            mode = stat.S_IMODE(cred_file.stat().st_mode)
            assert mode == 0o600  # Owner read/write only

    def test_login_overwrite_existing(self, runner, mock_user, tmp_path):
        """Test overwriting existing credentials."""
        cred_file = tmp_path / "credentials"
        cred_file.write_text("TONIE_USERNAME=old@example.com\nTONIE_PASSWORD=oldpass\n")

        with (
            patch("tonie_api.cli.commands.TonieAPI") as mock_api_class,
            patch("tonie_api.cli.commands.CONFIG_DIR", tmp_path),
            patch("tonie_api.cli.commands.CREDENTIALS_FILE", cred_file),
        ):
            mock_api = MagicMock()
            mock_api.get_me.return_value = mock_user
            mock_api_class.return_value = mock_api

            # Answer yes to overwrite
            result = runner.invoke(cli, ["login"], input="y\nnew@example.com\nnewpass\n")

            assert result.exit_code == 0
            content = cred_file.read_text()
            assert "TONIE_USERNAME=new@example.com" in content


class TestLogoutCommand:
    """Tests for the logout command."""

    def test_logout_success(self, runner, tmp_path):
        """Test successful logout command."""
        cred_file = tmp_path / "credentials"
        cred_file.write_text("TONIE_USERNAME=test@example.com\nTONIE_PASSWORD=secret\n")

        with patch("tonie_api.cli.commands.CREDENTIALS_FILE", cred_file):
            result = runner.invoke(cli, ["logout"])

            assert result.exit_code == 0
            assert "gelöscht" in result.output
            assert not cred_file.exists()

    def test_logout_no_credentials(self, runner, tmp_path):
        """Test logout command when no credentials file exists."""
        cred_file = tmp_path / "credentials"

        with patch("tonie_api.cli.commands.CREDENTIALS_FILE", cred_file):
            result = runner.invoke(cli, ["logout"])

            assert result.exit_code == 0
            assert "Keine gespeicherten Zugangsdaten" in result.output


class TestGlobalOptions:
    """Tests for global CLI options."""

    def test_username_password_options(self, runner, mock_user):
        """Test that username and password options are passed to API."""
        with patch("tonie_api.cli.commands.TonieAPI") as mock_api_class:
            mock_api = MagicMock()
            mock_api.get_me.return_value = mock_user
            mock_api_class.return_value = mock_api

            result = runner.invoke(cli, ["-u", "user@example.com", "-p", "secret", "me"])

            assert result.exit_code == 0
            mock_api_class.assert_called_once_with(username="user@example.com", password="secret")
