"""CLI commands for tonie-api."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

import click
import questionary

from tonie_api import TonieAPI
from tonie_api.cli.i18n import t
from tonie_api.cli.output import (
    create_progress,
    print_error,
    print_json,
    print_success,
    print_table,
)
from tonie_api.exceptions import AuthenticationError, TonieAPIError

REPO_URL = "git+https://github.com/Julschik/toniebox-api.git"

CONFIG_DIR = Path.home() / ".config" / "tonie-api"
CREDENTIALS_FILE = CONFIG_DIR / "credentials"

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
        raise click.ClickException(t("cli.error.no_households"))
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
        print_error(t("cli.error.api", error=str(e)))
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
                click.echo(t("cli.households.empty"))
                return
            print_table(
                ["ID", "Name", "Owner", "Access"],
                [household_to_row(h) for h in items],
            )
    except TonieAPIError as e:
        print_error(t("cli.error.api", error=str(e)))
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
            print_json([item.model_dump(by_alias=True) for item in items])
        else:
            if not items:
                click.echo(t("cli.tonies.empty"))
                return
            print_table(
                ["ID", "Name", "Chapters", "Duration", "Remaining"],
                [tonie_to_row(item) for item in items],
            )
    except TonieAPIError as e:
        print_error(t("cli.error.api", error=str(e)))
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

        click.echo(t("cli.upload.uploading", filename=file.name))

        # Get upload URL
        upload_request = api.request_file_upload()

        # Upload to S3 with progress bar
        file_size = file.stat().st_size

        with create_progress() as progress:
            task = progress.add_task(t("cli.upload.cloud_upload"), total=file_size)

            def progress_callback(bytes_sent: int, _total_bytes: int) -> None:
                progress.update(task, completed=bytes_sent)

            api.upload_to_s3(file, upload_request, progress_callback=progress_callback)

        # Add chapter
        chapter_title = title or file.stem
        click.echo(t("cli.upload.adding_chapter", title=chapter_title))
        tonie = api.add_chapter(resolved_household, tonie_id, chapter_title, upload_request.file_id)

        if ctx.obj.get("json"):
            print_json(tonie.model_dump(by_alias=True))
        else:
            print_success(t("cli.upload.success", title=chapter_title, tonie_name=tonie.name))
            click.echo(t("cli.upload.total_chapters", count=tonie.chapters_present))
            click.echo(
                t(
                    "cli.upload.duration_info",
                    duration=f"{tonie.seconds_present:.0f}",
                    remaining=f"{tonie.seconds_remaining:.0f}",
                ),
            )
    except TonieAPIError as e:
        print_error(t("cli.error.api", error=str(e)))
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
            print_success(t("cli.shuffle.success", count=tonie.chapters_present, name=tonie.name))
    except TonieAPIError as e:
        print_error(t("cli.error.api", error=str(e)))
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
            click.echo(t("cli.clear.no_chapters", name=tonie.name))
            return

        if not yes:
            click.confirm(
                t("cli.clear.confirm", count=tonie.chapters_present, name=tonie.name),
                abort=True,
            )

        tonie = api.clear_chapters(resolved_household, tonie_id)

        if ctx.obj.get("json"):
            print_json(tonie.model_dump(by_alias=True))
        else:
            print_success(t("cli.clear.success", name=tonie.name))
    except TonieAPIError as e:
        print_error(t("cli.error.api", error=str(e)))
        ctx.exit(1)


@click.command()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Show backend configuration and limits."""
    try:
        api = get_api(ctx)
        cfg = api.get_config()

        if ctx.obj.get("json"):
            print_json(cfg.model_dump(by_alias=True))
        else:
            minutes = cfg.max_seconds // 60
            mb = cfg.max_bytes / (1024 * 1024)
            click.echo(t("cli.config.title"))
            click.echo(t("cli.config.max_chapters", count=cfg.max_chapters))
            click.echo(t("cli.config.max_duration", minutes=minutes, seconds=cfg.max_seconds))
            click.echo(t("cli.config.max_size", mb=mb))
            click.echo(t("cli.config.formats", formats=", ".join(cfg.accepts)))
    except TonieAPIError as e:
        print_error(t("cli.error.api", error=str(e)))
        ctx.exit(1)


@click.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Check API reachability."""
    try:
        api = get_api(ctx)
        start = time.time()
        api.get_me()
        latency = (time.time() - start) * 1000

        if ctx.obj.get("json"):
            print_json({"status": "ok", "latency_ms": round(latency)})
        else:
            print_success(t("cli.status.success", latency=latency))
    except TonieAPIError as e:
        if ctx.obj.get("json"):
            print_json({"status": "error", "message": str(e)})
        else:
            print_error(t("cli.status.error", error=str(e)))
        ctx.exit(1)


@click.command()
@click.pass_context
def login(ctx: click.Context) -> None:
    """Save your Tonie Cloud credentials.

    Credentials are stored in ~/.config/tonie-api/credentials
    """
    click.echo(f"🎵 {t('cli.login.title')}")
    click.echo("=" * 40)
    click.echo()

    # Check if already logged in
    if CREDENTIALS_FILE.exists():
        click.echo(t("cli.login.already_logged_in"))
        if not click.confirm(t("cli.login.overwrite_confirm")):
            return

    click.echo(t("cli.login.prompt"))
    click.echo()

    username = click.prompt(t("cli.login.email_prompt"))
    password = click.prompt(t("cli.login.password_prompt"), hide_input=True)

    # Verify credentials
    click.echo()
    click.echo(t("cli.login.verifying"))

    try:
        api = TonieAPI(username=username, password=password)
        user = api.get_me()
        click.echo()
        print_success(t("cli.login.success", email=user.email))
    except AuthenticationError:
        click.echo()
        print_error(t("cli.login.invalid_creds"))
        ctx.exit(1)
    except TonieAPIError as e:
        click.echo()
        print_error(t("cli.login.connection_error", error=str(e)))
        ctx.exit(1)

    # Save credentials
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(
        f"TONIE_USERNAME={username}\nTONIE_PASSWORD={password}\n",
        encoding="utf-8",
    )
    # Set restrictive permissions (owner read/write only)
    CREDENTIALS_FILE.chmod(0o600)

    click.echo()
    click.echo(f"✓ {t('cli.login.saved')}")
    click.echo()
    click.echo(t("cli.login.help_commands"))


@click.command()
@click.pass_context
def logout(_ctx: click.Context) -> None:
    """Remove saved credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        print_success(t("cli.logout.success"))
    else:
        click.echo(t("cli.logout.not_found"))


# Preset commands
@click.group()
def preset() -> None:
    """Manage presets for automated workflows."""


@preset.command("list")
@click.pass_context
def preset_list(ctx: click.Context) -> None:
    """List all available presets."""
    from tonie_api.presets import load_presets

    presets = load_presets()

    if ctx.obj.get("json"):
        print_json(presets)
    else:
        if not presets:
            click.echo(t("cli.preset.list.empty"))
            click.echo(t("cli.preset.list.create_hint"))
            return

        print_table(
            ["Name", "Beschreibung", "Aktionen"],
            [
                [name, p.get("description", "-"), str(len(p.get("actions", [])))]
                for name, p in presets.items()
            ],
        )


@preset.command("run")
@click.argument("name")
@click.pass_context
def preset_run(ctx: click.Context, name: str) -> None:
    """Run a preset.

    NAME is the preset name.
    """
    from tonie_api.presets import PresetError, run_preset

    try:
        api = get_api(ctx)
        click.echo(t("cli.preset.run.starting", name=name))

        results = run_preset(api, name)

        if ctx.obj.get("json"):
            print_json(results)
        else:
            for result in results:
                result_status = result["status"]
                action = result["action"]
                target = result["target"]

                if result_status == "success":
                    print_success(t("cli.preset.run.action_success", action=action, target=target))
                else:
                    print_error(
                        t(
                            "cli.preset.run.action_error",
                            action=action,
                            target=target,
                            error=result.get("error", ""),
                        ),
                    )

            successful = sum(1 for r in results if r["status"] == "success")
            click.echo(f"\n{t('cli.preset.run.summary', successful=successful, total=len(results))}")

    except PresetError as e:
        print_error(t("cli.error.preset", error=str(e)))
        ctx.exit(1)
    except TonieAPIError as e:
        print_error(t("cli.error.api", error=str(e)))
        ctx.exit(1)


@preset.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Preset description")
@click.pass_context
def preset_create(ctx: click.Context, name: str, description: str) -> None:  # noqa: ARG001
    """Create a new preset interactively.

    NAME is the preset name.
    """
    from tonie_api.presets import create_preset, load_presets

    # Check if preset already exists
    presets = load_presets()
    if name in presets and not click.confirm(t("cli.preset.create.exists_confirm", name=name)):
        return

    if not description:
        description = questionary.text(t("cli.preset.create.description_prompt")).ask() or ""

    actions: list[dict] = []
    click.echo(f"\n{t('cli.preset.create.add_actions')}\n")

    while True:
        action_type = questionary.select(
            t("cli.preset.create.action_type_prompt"),
            choices=["shuffle", "upload", "clear", t("cli.preset.create.action_done")],
        ).ask()

        if action_type == t("cli.preset.create.action_done") or action_type is None:
            break

        target = questionary.text(
            t("cli.preset.create.target_prompt"),
            default="all" if action_type in ("shuffle", "clear") else "",
        ).ask()

        if not target:
            continue

        action = {"type": action_type, "target": target}

        if action_type == "upload":
            source = questionary.path(t("cli.preset.create.source_prompt")).ask()
            if source:
                action["source"] = source

        actions.append(action)
        click.echo(t("cli.preset.create.action_added", action_type=action_type, target=target))

    if not actions:
        click.echo(t("cli.preset.create.no_actions"))
        return

    create_preset(name, description, actions)
    print_success(t("cli.preset.create.success", name=name, count=len(actions)))


@preset.command("delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def preset_delete(ctx: click.Context, name: str, yes: bool) -> None:
    """Delete a preset.

    NAME is the preset name.
    """
    from tonie_api.presets import PresetError, delete_preset, get_preset

    try:
        preset_data = get_preset(name)
        if not yes:
            actions_count = len(preset_data.get("actions", []))
            click.confirm(t("cli.preset.delete.confirm", name=name, count=actions_count), abort=True)

        delete_preset(name)
        print_success(t("cli.preset.delete.success", name=name))
    except PresetError as e:
        print_error(str(e))
        ctx.exit(1)


@click.command()
@click.pass_context
def interactive(ctx: click.Context) -> None:
    """Interactive mode with menu navigation."""
    try:
        api = get_api(ctx)
        households_list = api.get_households()
        if not households_list:
            print_error(t("cli.error.no_households"))
            ctx.exit(1)
            return

        household_id = households_list[0].id

        while True:
            action = questionary.select(
                t("cli.interactive.prompt"),
                choices=[
                    t("cli.interactive.show_tonies"),
                    t("cli.interactive.upload"),
                    t("cli.interactive.shuffle"),
                    t("cli.interactive.clear_chapters"),
                    t("cli.interactive.run_preset"),
                    t("cli.interactive.exit"),
                ],
            ).ask()

            if action is None or action == t("cli.interactive.exit"):
                click.echo(t("cli.interactive.goodbye"))
                break

            if action == t("cli.interactive.show_tonies"):
                _interactive_show_tonies(api, household_id, ctx)
            elif action == t("cli.interactive.upload"):
                _interactive_upload(api, household_id, ctx)
            elif action == t("cli.interactive.shuffle"):
                _interactive_shuffle(api, household_id)
            elif action == t("cli.interactive.clear_chapters"):
                _interactive_clear(api, household_id)
            elif action == t("cli.interactive.run_preset"):
                _interactive_run_preset(api)

            click.echo()

    except TonieAPIError as e:
        print_error(t("cli.error.api", error=str(e)))
        ctx.exit(1)


def _interactive_show_tonies(api: TonieAPI, household_id: str, ctx: click.Context) -> None:
    """Show tonies in interactive mode."""
    items = api.get_creative_tonies(household_id)
    if not items:
        click.echo(t("cli.interactive.no_tonies"))
        return

    if ctx.obj.get("json"):
        print_json([item.model_dump(by_alias=True) for item in items])
    else:
        print_table(
            ["ID", "Name", "Chapters", "Duration", "Remaining"],
            [tonie_to_row(item) for item in items],
        )


def _interactive_upload(api: TonieAPI, household_id: str, ctx: click.Context) -> None:
    """Upload file in interactive mode."""
    items = api.get_creative_tonies(household_id)
    if not items:
        click.echo(t("cli.interactive.no_tonies"))
        return

    tonie_choices = [f"{item.name} ({item.id})" for item in items]
    selected = questionary.select(t("cli.interactive.select_tonie"), choices=tonie_choices).ask()

    if not selected:
        return

    # Extract tonie ID from selection
    tonie_id = selected.split("(")[-1].rstrip(")")

    file_path = questionary.path(t("cli.interactive.select_file")).ask()
    if not file_path or not Path(file_path).exists():
        return

    file = Path(file_path)
    file_size = file.stat().st_size

    click.echo(t("cli.upload.uploading", filename=file.name))

    upload_request = api.request_file_upload()

    with create_progress() as progress:
        task = progress.add_task(t("cli.upload.cloud_upload"), total=file_size)

        def progress_callback(bytes_sent: int, _total_bytes: int) -> None:
            progress.update(task, completed=bytes_sent)

        api.upload_to_s3(file, upload_request, progress_callback=progress_callback)

    chapter_title = file.stem
    click.echo(t("cli.upload.adding_chapter", title=chapter_title))
    tonie = api.add_chapter(household_id, tonie_id, chapter_title, upload_request.file_id)

    if ctx.obj.get("json"):
        print_json(tonie.model_dump(by_alias=True))
    else:
        print_success(t("cli.upload.success", title=chapter_title, tonie_name=tonie.name))


def _interactive_shuffle(api: TonieAPI, household_id: str) -> None:
    """Shuffle in interactive mode."""
    items = api.get_creative_tonies(household_id)
    if not items:
        click.echo(t("cli.interactive.no_tonies"))
        return

    tonie_choices = [f"{item.name} ({item.id})" for item in items]
    selected = questionary.select(t("cli.interactive.select_tonie"), choices=tonie_choices).ask()

    if not selected:
        return

    tonie_id = selected.split("(")[-1].rstrip(")")
    tonie = api.shuffle_chapters(household_id, tonie_id)
    print_success(t("cli.shuffle.success", count=tonie.chapters_present, name=tonie.name))


def _interactive_clear(api: TonieAPI, household_id: str) -> None:
    """Clear chapters in interactive mode."""
    items = api.get_creative_tonies(household_id)
    if not items:
        click.echo(t("cli.interactive.no_tonies"))
        return

    tonie_choices = [f"{item.name} ({item.id})" for item in items]
    selected = questionary.select(t("cli.interactive.select_tonie"), choices=tonie_choices).ask()

    if not selected:
        return

    tonie_id = selected.split("(")[-1].rstrip(")")
    tonie = api.get_creative_tonie(household_id, tonie_id)

    if tonie.chapters_present == 0:
        click.echo(t("cli.clear.no_chapters", name=tonie.name))
        return

    if click.confirm(t("cli.clear.confirm", count=tonie.chapters_present, name=tonie.name)):
        tonie = api.clear_chapters(household_id, tonie_id)
        print_success(t("cli.clear.success", name=tonie.name))


@click.command()
@click.option("--force", "-f", is_flag=True, help="Update without confirmation")
@click.pass_context
def update(ctx: click.Context, force: bool) -> None:
    """Update tonie-api to the latest version from GitHub."""
    import subprocess
    import sys

    if not force:
        click.confirm(t("cli.update.confirm"), abort=True)

    click.echo(t("cli.update.updating"))

    try:
        result = subprocess.run(  # noqa: S603 (REPO_URL is a trusted constant)
            [sys.executable, "-m", "pip", "install", "--upgrade", REPO_URL],
            capture_output=True,
            text=True,
            check=True,
        )
        if ctx.obj.get("debug"):
            click.echo(result.stdout)
        print_success(t("cli.update.success"))
        click.echo(t("cli.update.restart_hint"))
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        print_error(t("cli.update.failed", error=error_msg))
        ctx.exit(1)


def _interactive_run_preset(api: TonieAPI) -> None:
    """Run preset in interactive mode."""
    from tonie_api.presets import PresetError, load_presets, run_preset

    presets = load_presets()
    if not presets:
        click.echo(t("cli.interactive.no_presets"))
        return

    preset_choices = list(presets.keys())
    selected = questionary.select(t("cli.interactive.select_preset"), choices=preset_choices).ask()

    if not selected:
        return

    try:
        click.echo(t("cli.preset.run.starting", name=selected))
        results = run_preset(api, selected)

        for result in results:
            result_status = result["status"]
            action = result["action"]
            target = result["target"]

            if result_status == "success":
                print_success(t("cli.preset.run.action_success", action=action, target=target))
            else:
                print_error(
                    t(
                        "cli.preset.run.action_error",
                        action=action,
                        target=target,
                        error=result.get("error", ""),
                    ),
                )

        successful = sum(1 for r in results if r["status"] == "success")
        click.echo(t("cli.preset.run.summary", successful=successful, total=len(results)))
    except PresetError as e:
        print_error(t("cli.error.preset", error=str(e)))
