"""Chapter list widget for displaying Tonie chapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import VerticalScroll
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from tonie_api.models import Chapter


def format_duration(seconds: float) -> str:
    """Format duration in seconds to mm:ss format.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted duration string.
    """
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"


class ChapterItem(Static):
    """Single chapter item display."""

    def __init__(
        self,
        chapter: Chapter,
        index: int,
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize chapter item.

        Args:
            chapter: Chapter data.
            index: Chapter index (1-based).
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._chapter = chapter
        self._index = index

    def compose(self) -> ComposeResult:
        """Compose the chapter item."""
        duration = format_duration(self._chapter.seconds)
        transcoding = " [transcoding]" if self._chapter.transcoding else ""
        yield Static(
            f"{self._index}. {self._chapter.title} ({duration}){transcoding}",
            classes="chapter-item",
        )


class ChapterList(VerticalScroll):
    """Scrollable list of chapters for a Creative Tonie."""

    def __init__(
        self,
        chapters: list[Chapter] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,  # noqa: A002
        classes: str | None = None,
    ) -> None:
        """Initialize chapter list.

        Args:
            chapters: Initial list of chapters.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._chapters = chapters or []

    def compose(self) -> ComposeResult:
        """Compose the chapter list."""
        if not self._chapters:
            yield Static("Keine Kapitel vorhanden", classes="chapter-empty")
        else:
            for i, chapter in enumerate(self._chapters, 1):
                yield ChapterItem(chapter, i)

    def update_chapters(self, chapters: list[Chapter]) -> None:
        """Update the chapter list.

        Args:
            chapters: New list of chapters.
        """
        self._chapters = chapters
        self.remove_children()

        if not chapters:
            self.mount(Static("Keine Kapitel vorhanden", classes="chapter-empty"))
        else:
            for i, chapter in enumerate(chapters, 1):
                self.mount(ChapterItem(chapter, i))
