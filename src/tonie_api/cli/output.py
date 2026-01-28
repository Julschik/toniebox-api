"""Output formatting utilities for the CLI."""

from __future__ import annotations

import json
from typing import Any

import click


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print data as a formatted ASCII table.

    Args:
        headers: List of column headers.
        rows: List of rows, each row is a list of values.
    """
    if not rows:
        click.echo("No data.")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Build format string
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)

    # Print header
    click.echo(fmt.format(*headers))
    click.echo(fmt.format(*("-" * w for w in widths)))

    # Print rows
    for row in rows:
        click.echo(fmt.format(*row))


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
    click.secho(message, fg="green")


def print_error(message: str) -> None:
    """Print an error message in red.

    Args:
        message: The message to print.
    """
    click.secho(message, fg="red", err=True)


def print_warning(message: str) -> None:
    """Print a warning message in yellow.

    Args:
        message: The message to print.
    """
    click.secho(message, fg="yellow", err=True)
