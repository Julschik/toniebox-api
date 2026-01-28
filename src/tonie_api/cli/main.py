"""Main CLI entry point for tonie-api."""

from __future__ import annotations

import logging

import click

from tonie_api.cli.commands import (
    clear,
    config,
    households,
    interactive,
    login,
    logout,
    me,
    preset,
    shuffle,
    status,
    tonies,
    update,
    upload,
)
from tonie_api.cli.i18n import load_locale


@click.group(invoke_without_command=True)
@click.option(
    "--username",
    "-u",
    envvar=["TONIE_USERNAME"],
    help="Tonie Cloud username (or TONIE_USERNAME env)",
)
@click.option(
    "--password",
    "-p",
    envvar=["TONIE_PASSWORD"],
    help="Tonie Cloud password (or TONIE_PASSWORD env)",
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON instead of table")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option(
    "--lang",
    default="de",
    type=click.Choice(["de", "en"]),
    help="Language (de/en)",
)
@click.pass_context
def cli(  # noqa: PLR0913
    ctx: click.Context,
    username: str | None,
    password: str | None,
    json_output: bool,
    debug: bool,
    lang: str,
) -> None:
    """Tonie Cloud CLI - Manage your Creative Tonies from the command line.

    Run without arguments to start the interactive TUI.
    """
    # Load locale
    load_locale(lang)

    # Configure debug logging
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    ctx.ensure_object(dict)
    ctx.obj["username"] = username
    ctx.obj["password"] = password
    ctx.obj["json"] = json_output
    ctx.obj["debug"] = debug
    ctx.obj["lang"] = lang

    # If no subcommand provided, launch TUI
    if ctx.invoked_subcommand is None:
        from tonie_api.tui import main as tui_main

        tui_main()


# Register commands
cli.add_command(login)
cli.add_command(logout)
cli.add_command(me)
cli.add_command(households)
cli.add_command(tonies)
cli.add_command(upload)
cli.add_command(shuffle)
cli.add_command(clear)
cli.add_command(config)
cli.add_command(status)
cli.add_command(preset)
cli.add_command(interactive)
cli.add_command(update)


if __name__ == "__main__":
    cli()
