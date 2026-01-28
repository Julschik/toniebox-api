"""Tests for TUI widgets."""

from __future__ import annotations

from dataclasses import dataclass

from tonie_api.tui.widgets.chapter_list import ChapterList, format_duration


class TestFormatDuration:
    """Tests for the format_duration function."""

    def test_format_zero(self) -> None:
        """Test formatting zero seconds."""
        assert format_duration(0) == "0:00"

    def test_format_seconds_only(self) -> None:
        """Test formatting less than a minute."""
        assert format_duration(45) == "0:45"
        assert format_duration(5) == "0:05"

    def test_format_minutes(self) -> None:
        """Test formatting minutes and seconds."""
        assert format_duration(60) == "1:00"
        assert format_duration(90) == "1:30"
        assert format_duration(125) == "2:05"

    def test_format_large_values(self) -> None:
        """Test formatting large durations."""
        assert format_duration(3600) == "60:00"  # 1 hour
        assert format_duration(3661) == "61:01"

    def test_format_float_seconds(self) -> None:
        """Test formatting float values (should truncate)."""
        assert format_duration(90.5) == "1:30"
        assert format_duration(90.9) == "1:30"


class TestChapterList:
    """Tests for ChapterList widget."""

    @dataclass
    class MockChapter:
        """Mock chapter for testing."""

        title: str
        seconds: float
        transcoding: bool = False

    def test_init_empty(self) -> None:
        """Test initializing with no chapters."""
        widget = ChapterList()
        assert widget._chapters == []

    def test_init_with_chapters(self) -> None:
        """Test initializing with chapters."""
        chapters = [self.MockChapter("Track 1", 180)]
        widget = ChapterList(chapters=chapters)  # type: ignore[arg-type]
        assert widget._chapters == chapters

    def test_update_chapters(self) -> None:
        """Test updating chapters."""
        widget = ChapterList()
        chapters = [
            self.MockChapter("Track 1", 180),
            self.MockChapter("Track 2", 240),
        ]
        # We can't fully test compose without a running app, but we can test the state update
        widget._chapters = chapters
        assert len(widget._chapters) == 2
        assert widget._chapters[0].title == "Track 1"


class TestSidebar:
    """Tests for Sidebar navigation."""

    def test_nav_items_structure(self) -> None:
        """Test that NAV_ITEMS has expected structure."""
        from tonie_api.tui.widgets.sidebar import Sidebar

        items = Sidebar.NAV_ITEMS
        assert len(items) == 5

        # Check home is first
        assert items[0].id == "home"
        assert items[0].key == "1"

        # Check all items have required fields
        for item in items:
            assert item.id
            assert item.label
            assert item.key


class TestErrorModal:
    """Tests for ErrorModal widget."""

    def test_init_with_defaults(self) -> None:
        """Test ErrorModal initialization with default title."""
        from tonie_api.tui.widgets.error_modal import ErrorModal

        modal = ErrorModal("Test error message")
        assert modal._message == "Test error message"
        assert modal._title == "Fehler"

    def test_init_with_custom_title(self) -> None:
        """Test ErrorModal initialization with custom title."""
        from tonie_api.tui.widgets.error_modal import ErrorModal

        modal = ErrorModal("Test error", title="Custom Title")
        assert modal._message == "Test error"
        assert modal._title == "Custom Title"


class TestConfirmModal:
    """Tests for ConfirmModal widget."""

    def test_init_with_defaults(self) -> None:
        """Test ConfirmModal initialization with default title."""
        from tonie_api.tui.widgets.error_modal import ConfirmModal

        modal = ConfirmModal("Are you sure?")
        assert modal._message == "Are you sure?"
        assert modal._title == "Bestätigen"

    def test_init_with_custom_title(self) -> None:
        """Test ConfirmModal initialization with custom title."""
        from tonie_api.tui.widgets.error_modal import ConfirmModal

        modal = ConfirmModal("Delete item?", title="Confirm Delete")
        assert modal._message == "Delete item?"
        assert modal._title == "Confirm Delete"

    def test_bindings(self) -> None:
        """Test that ConfirmModal has expected bindings."""
        from tonie_api.tui.widgets.error_modal import ConfirmModal

        bindings = ConfirmModal.BINDINGS
        binding_keys = [b[0] for b in bindings]

        assert "escape" in binding_keys
        assert "y" in binding_keys
        assert "n" in binding_keys
