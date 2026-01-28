"""CLI commands for tonie-api."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

from tonie_api import TonieAPI
from tonie_api.cli.output import print_error, print_json, print_success, print_table
from tonie_api.exceptions import TonieAPIError

if TYPE_CHECKING:
    from tonie_api.models import CreativeTonie, Household


def get_api(ctx: click.Context) -> TonieAPI:
    """Get or create TonieAPI instance from context.

    Args:
        ctx: Click context with credentials.

    Returns:
        TonieAPI instance.
    """
    if "api" not in ctx.obj:
        ctx.obj["api"] = TonieAPI(
            username=ctx.obj.get("username"),
            password=ctx.obj.get("password"),
        )
    return ctx.obj["api"]


def resolve_household_id(ctx: click.Context, household_id: str | None) -> str:
    """Resolve household ID, using first household if not provided.

    Args:
        ctx: Click context.
        household_id: Optional household ID.

    Returns:
        Resolved household ID.

    Raises:
        click.ClickException: If no households found.
    """
    if household_id:
        return household_id

    api = get_api(ctx)
    households = api.get_households()
    if not households:
        raise click.ClickException("No households found")
    return households[0].id


def household_to_row(h: Household) -> list[str]:
    """Convert Household to table row."""
    return [h.id, h.name, h.owner_name, h.access]


def tonie_to_row(t: CreativeTonie) -> list[str]:
    """Convert CreativeTonie to table row."""
    return [
        t.id,
        t.name,
        str(t.chapters_present),
        f"{t.seconds_present:.0f}s",
        f"{t.seconds_remaining:.0f}s",
    ]


@click.command()
@click.pass_context
def me(ctx: click.Context) -> None:
    """Show current user information."""
    try:
        api = get_api(ctx)
        user = api.get_me()

        if ctx.obj.get("json"):
            print_json({"uuid": user.uuid, "email": user.email})
        else:
            click.echo(f"UUID:  {user.uuid}")
            click.echo(f"Email: {user.email}")
    except TonieAPIError as e:
        print_error(f"API Error: {e}")
        ctx.exit(1)


@click.command()
@click.pass_context
def households(ctx: click.Context) -> None:
    """List all households."""
    try:
        api = get_api(ctx)
        items = api.get_households()

        if ctx.obj.get("json"):
            print_json([h.model_dump(by_alias=True) for h in items])
        else:
            if not items:
                click.echo("No households found.")
                return
            print_table(
                ["ID", "Name", "Owner", "Access"],
                [household_to_row(h) for h in items],
            )
    except TonieAPIError as e:
        print_error(f"API Error: {e}")
        ctx.exit(1)


@click.command()
@click.argument("household_id", required=False)
@click.pass_context
def tonies(ctx: click.Context, household_id: str | None) -> None:
    """List Creative Tonies in a household.

    If HOUSEHOLD_ID is not provided, uses the first household.
    """
    try:
        api = get_api(ctx)
        resolved_id = resolve_household_id(ctx, household_id)
        items = api.get_creative_tonies(resolved_id)

        if ctx.obj.get("json"):
            print_json([t.model_dump(by_alias=True) for t in items])
        else:
            if not items:
                click.echo("No Creative Tonies found.")
                return
            print_table(
                ["ID", "Name", "Chapters", "Duration", "Remaining"],
                [tonie_to_row(t) for t in items],
            )
    except TonieAPIError as e:
        print_error(f"API Error: {e}")
        ctx.exit(1)


@click.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.argument("tonie_id")
@click.option("--title", "-t", help="Chapter title (defaults to filename)")
@click.option("--household", "-h", "household_id", help="Household ID (defaults to first household)")
@click.pass_context
def upload(
    ctx: click.Context,
    file: Path,
    tonie_id: str,
    title: str | None,
    household_id: str | None,
) -> None:
    """Upload an audio file to a Creative Tonie.

    FILE is the path to the audio file.
    TONIE_ID is the Creative Tonie ID.
    """
    try:
        api = get_api(ctx)
        resolved_household = resolve_household_id(ctx, household_id)

        click.echo(f"Uploading {file.name}...")

        # Get upload URL
        upload_request = api.request_file_upload()

        # Upload to S3 with progress indication
        click.echo("Uploading to cloud storage...")
        api.upload_to_s3(file, upload_request)

        # Add chapter
        chapter_title = title or file.stem
        click.echo(f"Adding chapter '{chapter_title}'...")
        tonie = api.add_chapter(resolved_household, tonie_id, chapter_title, upload_request.file_id)

        if ctx.obj.get("json"):
            print_json(tonie.model_dump(by_alias=True))
        else:
            print_success(f"Uploaded '{chapter_title}' to {tonie.name}")
            click.echo(f"Total chapters: {tonie.chapters_present}")
            click.echo(f"Duration: {tonie.seconds_present:.0f}s / Remaining: {tonie.seconds_remaining:.0f}s")
    except TonieAPIError as e:
        print_error(f"API Error: {e}")
        ctx.exit(1)


@click.command()
@click.argument("tonie_id")
@click.option("--household", "-h", "household_id", help="Household ID (defaults to first household)")
@click.pass_context
def shuffle(ctx: click.Context, tonie_id: str, household_id: str | None) -> None:
    """Shuffle chapters of a Creative Tonie.

    TONIE_ID is the Creative Tonie ID.
    """
    try:
        api = get_api(ctx)
        resolved_household = resolve_household_id(ctx, household_id)

        tonie = api.shuffle_chapters(resolved_household, tonie_id)

        if ctx.obj.get("json"):
            print_json(tonie.model_dump(by_alias=True))
        else:
            print_success(f"Shuffled {tonie.chapters_present} chapters on '{tonie.name}'")
    except TonieAPIError as e:
        print_error(f"API Error: {e}")
        ctx.exit(1)


@click.command()
@click.argument("tonie_id")
@click.option("--household", "-h", "household_id", help="Household ID (defaults to first household)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def clear(ctx: click.Context, tonie_id: str, household_id: str | None, yes: bool) -> None:
    """Clear all chapters from a Creative Tonie.

    TONIE_ID is the Creative Tonie ID.
    """
    try:
        api = get_api(ctx)
        resolved_household = resolve_household_id(ctx, household_id)

        # Get current tonie info for confirmation
        tonie = api.get_creative_tonie(resolved_household, tonie_id)

        if tonie.chapters_present == 0:
            click.echo(f"'{tonie.name}' has no chapters to clear.")
            return

        if not yes:
            click.confirm(
                f"Clear {tonie.chapters_present} chapters from '{tonie.name}'?",
                abort=True,
            )

        tonie = api.clear_chapters(resolved_household, tonie_id)

        if ctx.obj.get("json"):
            print_json(tonie.model_dump(by_alias=True))
        else:
            print_success(f"Cleared all chapters from '{tonie.name}'")
    except TonieAPIError as e:
        print_error(f"API Error: {e}")
        ctx.exit(1)
