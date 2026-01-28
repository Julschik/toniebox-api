"""Preset management for automated Tonie workflows."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from tonie_api.api import TonieAPI

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".config" / "tonie-api"
PRESETS_FILE = CONFIG_DIR / "presets.yaml"


class PresetError(Exception):
    """Error in preset processing."""


def load_presets() -> dict[str, dict[str, Any]]:
    """Load presets from configuration file.

    Returns:
        Dictionary of preset name to preset configuration.
    """
    if not PRESETS_FILE.exists():
        return {}

    try:
        content = PRESETS_FILE.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
        return data.get("presets", {})
    except yaml.YAMLError as e:
        msg = f"Fehler beim Laden der Presets: {e}"
        raise PresetError(msg) from e


def save_presets(presets: dict[str, dict[str, Any]]) -> None:
    """Save presets to configuration file.

    Args:
        presets: Dictionary of preset configurations.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {"presets": presets}
    content = yaml.dump(data, default_flow_style=False, allow_unicode=True)
    PRESETS_FILE.write_text(content, encoding="utf-8")


def get_preset(name: str) -> dict[str, Any]:
    """Get a specific preset by name.

    Args:
        name: Preset name.

    Returns:
        Preset configuration.

    Raises:
        PresetError: If preset not found.
    """
    presets = load_presets()
    if name not in presets:
        msg = f"Preset '{name}' nicht gefunden"
        raise PresetError(msg)
    return presets[name]


def run_preset(api: TonieAPI, preset_name: str) -> list[dict[str, Any]]:
    """Execute a preset.

    Args:
        api: TonieAPI instance.
        preset_name: Name of the preset to run.

    Returns:
        List of action results.

    Raises:
        PresetError: If preset execution fails.
    """
    preset = get_preset(preset_name)
    actions = preset.get("actions", [])
    results: list[dict[str, Any]] = []

    households = api.get_households()
    if not households:
        msg = "Keine Haushalte gefunden"
        raise PresetError(msg)

    default_household_id = households[0].id

    for i, action in enumerate(actions):
        action_type = action.get("type")
        target = action.get("target")
        household_id = action.get("household", default_household_id)

        logger.debug("Executing action %d: %s on %s", i + 1, action_type, target)

        try:
            result = _execute_action(api, action_type, target, household_id, action)
            results.append({
                "action": action_type,
                "target": target,
                "status": "success",
                "result": result,
            })
        except Exception as e:  # noqa: BLE001
            results.append({
                "action": action_type,
                "target": target,
                "status": "error",
                "error": str(e),
            })
            logger.warning("Action %d failed: %s", i + 1, e)

    return results


def _execute_action(
    api: TonieAPI,
    action_type: str,
    target: str,
    household_id: str,
    action: dict[str, Any],
) -> dict[str, Any]:
    """Execute a single action.

    Args:
        api: TonieAPI instance.
        action_type: Type of action (shuffle, upload, clear).
        target: Target tonie ID or "all".
        household_id: Household ID.
        action: Full action configuration.

    Returns:
        Action result.

    Raises:
        PresetError: If action type is unknown.
    """
    if action_type == "shuffle":
        return _action_shuffle(api, target, household_id)
    if action_type == "clear":
        return _action_clear(api, target, household_id)
    if action_type == "upload":
        source = action.get("source")
        return _action_upload(api, target, household_id, source)

    msg = f"Unbekannter Aktionstyp: {action_type}"
    raise PresetError(msg)


def _action_shuffle(api: TonieAPI, target: str, household_id: str) -> dict[str, Any]:
    """Execute shuffle action.

    Args:
        api: TonieAPI instance.
        target: Tonie ID or "all".
        household_id: Household ID.

    Returns:
        Shuffle result.
    """
    if target == "all":
        tonies = api.get_creative_tonies(household_id)
        shuffled = []
        for tonie in tonies:
            if len(tonie.chapters) >= 2:  # noqa: PLR2004
                api.shuffle_chapters(household_id, tonie.id)
                shuffled.append(tonie.name)
        return {"shuffled": shuffled}

    tonie = api.shuffle_chapters(household_id, target)
    return {"shuffled": [tonie.name]}


def _action_clear(api: TonieAPI, target: str, household_id: str) -> dict[str, Any]:
    """Execute clear action.

    Args:
        api: TonieAPI instance.
        target: Tonie ID or "all".
        household_id: Household ID.

    Returns:
        Clear result.
    """
    if target == "all":
        tonies = api.get_creative_tonies(household_id)
        cleared = []
        for tonie in tonies:
            if tonie.chapters:
                api.clear_chapters(household_id, tonie.id)
                cleared.append(tonie.name)
        return {"cleared": cleared}

    tonie = api.clear_chapters(household_id, target)
    return {"cleared": [tonie.name]}


def _action_upload(
    api: TonieAPI,
    target: str,
    household_id: str,
    source: str | None,
) -> dict[str, Any]:
    """Execute upload action.

    Args:
        api: TonieAPI instance.
        target: Tonie ID.
        household_id: Household ID.
        source: Path to audio file or directory.

    Returns:
        Upload result.

    Raises:
        PresetError: If source is missing or invalid.
    """
    if not source:
        msg = "Upload-Aktion benötigt 'source' Parameter"
        raise PresetError(msg)

    source_path = Path(source).expanduser()
    if not source_path.exists():
        msg = f"Quelle nicht gefunden: {source_path}"
        raise PresetError(msg)

    uploaded = []

    if source_path.is_file():
        api.upload_audio_file(source_path, household_id, target)
        uploaded.append(source_path.name)
    elif source_path.is_dir():
        audio_files = list(source_path.glob("*.mp3")) + list(source_path.glob("*.m4a"))
        for audio_file in sorted(audio_files):
            api.upload_audio_file(audio_file, household_id, target)
            uploaded.append(audio_file.name)

    return {"uploaded": uploaded}


def create_preset(
    name: str,
    description: str,
    actions: list[dict[str, Any]],
) -> None:
    """Create a new preset.

    Args:
        name: Preset name.
        description: Preset description.
        actions: List of actions.
    """
    presets = load_presets()
    presets[name] = {
        "description": description,
        "actions": actions,
    }
    save_presets(presets)


def delete_preset(name: str) -> None:
    """Delete a preset.

    Args:
        name: Preset name.

    Raises:
        PresetError: If preset not found.
    """
    presets = load_presets()
    if name not in presets:
        msg = f"Preset '{name}' nicht gefunden"
        raise PresetError(msg)
    del presets[name]
    save_presets(presets)
