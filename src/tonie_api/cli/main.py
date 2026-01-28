"""Main CLI entry point for tonie-api."""

from __future__ import annotations

import click

from tonie_api.cli.commands import clear, households, me, shuffle, tonies, upload


@click.group()
@click.option("--username", "-u", envvar="USERNAME", help="Tonie Cloud username (or set USERNAME env var)")
@click.option("--password", "-p", envvar="PASSWORD", help="Tonie Cloud password (or set PASSWORD env var)")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON instead of table")
@click.pass_context
def cli(ctx: click.Context, username: str | None, password: str | None, json_output: bool) -> None:
    """Tonie Cloud CLI - Manage your Creative Tonies from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["username"] = username
    ctx.obj["password"] = password
    ctx.obj["json"] = json_output


# Register commands
cli.add_command(me)
cli.add_command(households)
cli.add_command(tonies)
cli.add_command(upload)
cli.add_command(shuffle)
cli.add_command(clear)


if __name__ == "__main__":
    cli()
