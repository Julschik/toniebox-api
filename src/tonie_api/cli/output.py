"""Output formatting utilities for the CLI."""

from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

console = Console()
error_console = Console(stderr=True)


def print_table(
    headers: list[str],
    rows: list[list[str]],
    title: str | None = None,
) -> None:
    """Print data as a formatted table using rich.

    Args:
        headers: List of column headers.
        rows: List of rows, each row is a list of values.
        title: Optional table title.
    """
    if not rows:
        click.echo("No data.")
        return

    table = Table(title=title, show_header=True, header_style="bold")

    for header in headers:
        table.add_column(header)

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)


def print_json(data: Any) -> None:
    """Print data as formatted JSON.

    Args:
        data: Data to serialize as JSON.
    """
    click.echo(json.dumps(data, indent=2, default=str))


def print_success(message: str) -> None:
    """Print a success message in green.

    Args:
        message: The message to print.
    """
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message in red.

    Args:
        message: The message to print.
    """
    error_console.print(f"[red]{message}[/red]")


def print_warning(message: str) -> None:
    """Print a warning message in yellow.

    Args:
        message: The message to print.
    """
    error_console.print(f"[yellow]{message}[/yellow]")


def create_progress() -> Progress:
    """Create a progress bar for file uploads.

    Returns:
        Rich Progress instance configured for uploads.
    """
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )
