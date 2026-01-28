"""Tests for the presets module."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from tonie_api.presets import (
    PresetError,
    create_preset,
    delete_preset,
    get_preset,
    load_presets,
    run_preset,
    save_presets,
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    with (
        patch("tonie_api.presets.CONFIG_DIR", tmp_path),
        patch("tonie_api.presets.PRESETS_FILE", tmp_path / "presets.yaml"),
    ):
        yield tmp_path


@pytest.fixture
def sample_presets():
    """Sample preset data."""
    return {
        "shuffle-all": {
            "description": "Shuffle all tonies",
            "actions": [
                {"type": "shuffle", "target": "all"},
            ],
        },
        "morning-routine": {
            "description": "Morning routine",
            "actions": [
                {"type": "shuffle", "target": "tonie-1"},
                {"type": "shuffle", "target": "tonie-2"},
            ],
        },
    }


class TestLoadPresets:
    """Tests for load_presets function."""

    def test_load_empty_when_no_file(self, temp_config_dir):  # noqa: ARG002
        """Test loading returns empty dict when no file."""
        result = load_presets()
        assert result == {}

    def test_load_presets_from_file(self, temp_config_dir, sample_presets):
        """Test loading presets from file."""
        presets_file = temp_config_dir / "presets.yaml"
        presets_file.write_text(yaml.dump({"presets": sample_presets}))

        result = load_presets()

        assert "shuffle-all" in result
        assert result["shuffle-all"]["description"] == "Shuffle all tonies"

    def test_load_presets_invalid_yaml(self, temp_config_dir):
        """Test loading invalid YAML raises PresetError."""
        presets_file = temp_config_dir / "presets.yaml"
        presets_file.write_text("invalid: yaml: content:")

        with pytest.raises(PresetError):
            load_presets()


class TestSavePresets:
    """Tests for save_presets function."""

    def test_save_creates_file(self, temp_config_dir, sample_presets):
        """Test saving creates presets file."""
        save_presets(sample_presets)

        presets_file = temp_config_dir / "presets.yaml"
        assert presets_file.exists()

    def test_save_and_load_roundtrip(self, temp_config_dir, sample_presets):  # noqa: ARG002
        """Test save and load produce same data."""
        save_presets(sample_presets)
        result = load_presets()

        assert result == sample_presets


class TestGetPreset:
    """Tests for get_preset function."""

    def test_get_existing_preset(self, temp_config_dir, sample_presets):  # noqa: ARG002
        """Test getting existing preset."""
        save_presets(sample_presets)

        result = get_preset("shuffle-all")

        assert result["description"] == "Shuffle all tonies"

    def test_get_nonexistent_preset(self, temp_config_dir):  # noqa: ARG002
        """Test getting nonexistent preset raises error."""
        with pytest.raises(PresetError, match="nicht gefunden"):
            get_preset("nonexistent")


class TestCreatePreset:
    """Tests for create_preset function."""

    def test_create_new_preset(self, temp_config_dir):  # noqa: ARG002
        """Test creating new preset."""
        create_preset(
            name="test-preset",
            description="Test description",
            actions=[{"type": "shuffle", "target": "all"}],
        )

        result = get_preset("test-preset")
        assert result["description"] == "Test description"
        assert len(result["actions"]) == 1

    def test_create_overwrites_existing(self, temp_config_dir, sample_presets):  # noqa: ARG002
        """Test creating preset overwrites existing."""
        save_presets(sample_presets)

        create_preset(
            name="shuffle-all",
            description="New description",
            actions=[],
        )

        result = get_preset("shuffle-all")
        assert result["description"] == "New description"


class TestDeletePreset:
    """Tests for delete_preset function."""

    def test_delete_existing_preset(self, temp_config_dir, sample_presets):  # noqa: ARG002
        """Test deleting existing preset."""
        save_presets(sample_presets)

        delete_preset("shuffle-all")

        presets = load_presets()
        assert "shuffle-all" not in presets
        assert "morning-routine" in presets

    def test_delete_nonexistent_preset(self, temp_config_dir):  # noqa: ARG002
        """Test deleting nonexistent preset raises error."""
        with pytest.raises(PresetError, match="nicht gefunden"):
            delete_preset("nonexistent")


class TestRunPreset:
    """Tests for run_preset function."""

    @pytest.fixture
    def mock_api(self):
        """Create mock API."""
        api = MagicMock()
        api.get_households.return_value = [MagicMock(id="hh-1")]
        return api

    def test_run_shuffle_all(self, temp_config_dir, mock_api, sample_presets):  # noqa: ARG002
        """Test running shuffle all preset."""
        save_presets(sample_presets)

        mock_api.get_creative_tonies.return_value = [
            MagicMock(id="t1", name="Tonie 1", chapters=[1, 2, 3]),
            MagicMock(id="t2", name="Tonie 2", chapters=[1, 2]),
        ]
        mock_api.shuffle_chapters.return_value = MagicMock(name="Shuffled")

        results = run_preset(mock_api, "shuffle-all")

        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert mock_api.shuffle_chapters.call_count == 2

    def test_run_preset_no_households(self, temp_config_dir, mock_api, sample_presets):  # noqa: ARG002
        """Test running preset with no households."""
        save_presets(sample_presets)
        mock_api.get_households.return_value = []

        with pytest.raises(PresetError, match="Keine Haushalte"):
            run_preset(mock_api, "shuffle-all")

    def test_run_preset_action_error(self, temp_config_dir, mock_api):  # noqa: ARG002
        """Test running preset with failing action."""
        create_preset("failing", "Failing preset", [{"type": "shuffle", "target": "tonie-1"}])

        mock_api.shuffle_chapters.side_effect = Exception("API Error")

        results = run_preset(mock_api, "failing")

        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "API Error" in results[0]["error"]

    def test_run_clear_action(self, temp_config_dir, mock_api):  # noqa: ARG002
        """Test running clear action."""
        create_preset("clear-one", "Clear preset", [{"type": "clear", "target": "tonie-1"}])

        mock_api.clear_chapters.return_value = MagicMock(name="Cleared")

        results = run_preset(mock_api, "clear-one")

        assert results[0]["status"] == "success"
        mock_api.clear_chapters.assert_called_once_with("hh-1", "tonie-1")

    def test_run_upload_action(self, temp_config_dir, mock_api):  # noqa: ARG002
        """Test running upload action."""
        # Create a temp audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio")
            audio_path = f.name

        try:
            create_preset(
                "upload-one",
                "Upload preset",
                [{"type": "upload", "target": "tonie-1", "source": audio_path}],
            )

            mock_api.upload_audio_file.return_value = MagicMock()

            results = run_preset(mock_api, "upload-one")

            assert results[0]["status"] == "success"
            mock_api.upload_audio_file.assert_called_once()
        finally:
            Path(audio_path).unlink()

    def test_run_upload_missing_source(self, temp_config_dir, mock_api):  # noqa: ARG002
        """Test running upload without source."""
        create_preset(
            "upload-no-source",
            "Upload without source",
            [{"type": "upload", "target": "tonie-1"}],
        )

        results = run_preset(mock_api, "upload-no-source")

        assert results[0]["status"] == "error"
        assert "source" in results[0]["error"].lower()

    def test_run_unknown_action(self, temp_config_dir, mock_api):  # noqa: ARG002
        """Test running unknown action type."""
        create_preset(
            "unknown-action",
            "Unknown action",
            [{"type": "unknown", "target": "tonie-1"}],
        )

        results = run_preset(mock_api, "unknown-action")

        assert results[0]["status"] == "error"
        assert "Unbekannter Aktionstyp" in results[0]["error"]
