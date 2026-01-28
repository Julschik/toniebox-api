"""Tests for CLI output formatting utilities."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from io import StringIO
from unittest.mock import patch

from rich.console import Console

from tonie_api.cli.output import (
    create_progress,
    print_error,
    print_json,
    print_success,
    print_table,
    print_warning,
)


class TestPrintTable:
    """Tests for print_table function."""

    def test_print_table_basic(self):
        """Test basic table printing."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)

        with patch("tonie_api.cli.output.console", console):
            headers = ["ID", "Name"]
            rows = [["1", "First"], ["2", "Second"]]
            print_table(headers, rows)

        result = output.getvalue()
        assert "ID" in result
        assert "Name" in result
        assert "First" in result
        assert "Second" in result

    def test_print_table_empty_rows(self, capsys):
        """Test table with empty rows."""
        headers = ["ID", "Name"]
        rows = []

        print_table(headers, rows)
        captured = capsys.readouterr()

        assert "No data." in captured.out

    def test_print_table_column_widths(self):
        """Test that columns are sized to fit content."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)

        with patch("tonie_api.cli.output.console", console):
            headers = ["Short", "Long Header"]
            rows = [["x", "y"], ["longer value", "z"]]
            print_table(headers, rows)

        result = output.getvalue()
        assert "Short" in result
        assert "Long Header" in result
        assert "longer value" in result

    def test_print_table_single_row(self):
        """Test table with single row."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)

        with patch("tonie_api.cli.output.console", console):
            headers = ["A", "B", "C"]
            rows = [["1", "2", "3"]]
            print_table(headers, rows)

        result = output.getvalue()
        assert "A" in result
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_print_table_with_title(self):
        """Test table with title."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)

        with patch("tonie_api.cli.output.console", console):
            headers = ["Header"]
            rows = [["value"]]
            print_table(headers, rows, title="My Table")

        result = output.getvalue()
        assert "My Table" in result
        assert "Header" in result
        assert "value" in result

    def test_print_table_special_characters(self):
        """Test table with special characters."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)

        with patch("tonie_api.cli.output.console", console):
            headers = ["Name", "Description"]
            rows = [["Test-Item", "Contains: special & chars!"]]
            print_table(headers, rows)

        result = output.getvalue()
        assert "Test-Item" in result
        assert "Contains: special & chars!" in result


class TestPrintJson:
    """Tests for print_json function."""

    def test_print_json_dict(self, capsys):
        """Test JSON output for dict."""
        data = {"key": "value", "number": 42}

        print_json(data)
        captured = capsys.readouterr()

        parsed = json.loads(captured.out)
        assert parsed == data

    def test_print_json_list(self, capsys):
        """Test JSON output for list."""
        data = [{"id": 1}, {"id": 2}]

        print_json(data)
        captured = capsys.readouterr()

        parsed = json.loads(captured.out)
        assert parsed == data

    def test_print_json_indented(self, capsys):
        """Test that JSON output is indented."""
        data = {"nested": {"key": "value"}}

        print_json(data)
        captured = capsys.readouterr()

        # Indented JSON has newlines
        assert "\n" in captured.out
        assert "  " in captured.out  # 2-space indent

    def test_print_json_non_serializable(self, capsys):
        """Test JSON output with non-serializable objects (uses str fallback)."""
        data = {"timestamp": datetime(2024, 1, 15, 10, 30, tzinfo=UTC)}

        print_json(data)
        captured = capsys.readouterr()

        # Should not raise, uses default=str
        assert "2024" in captured.out


class TestPrintSuccess:
    """Tests for print_success function."""

    def test_print_success_message(self):
        """Test success message output."""
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        with patch("tonie_api.cli.output.console", console):
            print_success("Operation completed successfully")

        result = output.getvalue()
        assert "Operation completed successfully" in result

    def test_print_success_empty_message(self):
        """Test success with empty message."""
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        with patch("tonie_api.cli.output.console", console):
            print_success("")

        # Should not crash
        result = output.getvalue()
        assert result is not None


class TestPrintError:
    """Tests for print_error function."""

    def test_print_error_message(self):
        """Test error message output."""
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        with patch("tonie_api.cli.output.error_console", console):
            print_error("Something went wrong")

        result = output.getvalue()
        assert "Something went wrong" in result

    def test_print_error_contains_message(self):
        """Test that error contains the message."""
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        with patch("tonie_api.cli.output.error_console", console):
            print_error("Error message")

        result = output.getvalue()
        assert "Error message" in result


class TestPrintWarning:
    """Tests for print_warning function."""

    def test_print_warning_message(self):
        """Test warning message output."""
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        with patch("tonie_api.cli.output.error_console", console):
            print_warning("This is a warning")

        result = output.getvalue()
        assert "This is a warning" in result

    def test_print_warning_contains_message(self):
        """Test that warning contains the message."""
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        with patch("tonie_api.cli.output.error_console", console):
            print_warning("Warning message")

        result = output.getvalue()
        assert "Warning message" in result


class TestCreateProgress:
    """Tests for create_progress function."""

    def test_create_progress_returns_progress(self):
        """Test that create_progress returns a Progress instance."""
        progress = create_progress()
        assert progress is not None
        # Progress is a context manager
        assert hasattr(progress, "__enter__")
        assert hasattr(progress, "__exit__")
