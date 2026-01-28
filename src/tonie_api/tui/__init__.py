"""Textual TUI for Tonie Cloud API.

This module provides an interactive terminal user interface for managing
Creative Tonies using the Textual framework.
"""

from __future__ import annotations

import sys

import click


def main() -> None:
    """Launch the Tonie Cloud TUI.

    Checks for interactive terminal before starting. Falls back to CLI
    if running in non-interactive environment (pipes, CI/CD).
    """
    if not sys.stdout.isatty():
        click.echo(
            "Error: TUI requires an interactive terminal.",
            err=True,
        )
        click.echo(
            "Use CLI commands instead: toniebox me, toniebox tonies, etc.",
            err=True,
        )
        sys.exit(1)

    from tonie_api.tui.app import TonieApp

    app = TonieApp()
    app.run()


__all__ = ["main"]
