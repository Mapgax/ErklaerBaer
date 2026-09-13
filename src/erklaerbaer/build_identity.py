"""Deterministic builds separate from immutable MINT source identities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .config import Settings
from .mascot_library import RIG_VERSION
from .models import TEMPLATES, Storyboard
from .speech_cache import digest_json


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_only(value):
    """Review bookkeeping never changes content identity."""
    omitted = {
        "created_at",
        "updated_at",
        "accessed_at",
        "review",
        "review_status",
        "approved",
        "owner_approved",
        "checked_at",
    }
    if isinstance(value, dict):
        return {k: content_only(v) for k, v in value.items() if k not in omitted}
    if isinstance(value, list):
        return [content_only(v) for v in value]
    return value


def build_payload(storyboard: Storyboard, settings: Settings) -> dict:
    root = settings.project_root
    code = Path(__file__).parent
    dependency_names = {
        "renderer.py",
        "models.py",
        "audio.py",
        "captions.py",
        "media.py",
        "mascot_library.py",
        "mechanisms.py",
        "visuals.py",
    }
    if storyboard.schema_version == "3":
        # collage_guitar holds the shared paper helpers every template draws with; each
        # template adds its own modules, so changing one never reuses a stale render.
        dependency_names |= {"collage_guitar.py", "expressive_speech.py"}
        for scene in storyboard.scenes:
            if scene.shot:
                dependency_names |= set(TEMPLATES[scene.shot.template_id].modules)
    renderer = {name: sha256(code / name) for name in sorted(dependency_names)}
    evidence_path = root / "docs" / "evidence" / f"{storyboard.experiment_id}.json"
    evidence = (
        content_only(json.loads(evidence_path.read_text())) if evidence_path.exists() else None
    )
    version = RIG_VERSION if storyboard.schema_version == "3" else "v2"
    manifest_path = root / f"assets/mascot/rig/{version}/manifest.json"
    manifest = (
        content_only(json.loads(manifest_path.read_text())) if manifest_path.exists() else None
    )
    assets = {}
    if manifest:
        for action in manifest["actions"].values():
            for frame in action["frames"]:
                path = (manifest_path.parent / frame["file"]).resolve()
                if not path.is_relative_to(manifest_path.parent.resolve()):
                    raise ValueError("Mascot file escapes library")
                assets[frame["file"]] = sha256(path)
                if assets[frame["file"]] != frame["sha256"]:
                    raise ValueError("Mascot checksum mismatch")
    if storyboard.schema_version == "3":
        texture = root / "assets/library/materials/v3/material-sheet.png"
        assets["collage-materials/v3"] = sha256(texture)
        # Every drawn-asset file a template pastes decides pixels, so each is hashed.
        for key, relative in (
            ("ear/v3", "assets/library/ear/v3/ear.png"),
            ("hands/v3", "assets/library/hands/v3/hand.png"),
        ):
            if (root / relative).exists():
                assets[key] = sha256(root / relative)
    from .renderer import SCHOOL_FONT, available_font_paths

    fonts = [sha256(p) if p else "pillow-default" for p in available_font_paths()]
    # Child-facing words are set in the school script; a font swap changes pixels.
    fonts.append(sha256(SCHOOL_FONT) if SCHOOL_FONT.exists() else "school-font-absent")
    return {
        "fonts": fonts,
        "storyboard": content_only(storyboard.model_dump(mode="json")),
        "evidence": evidence,
        "renderer": renderer,
        "mascot": manifest,
        "asset_hashes": assets,
        "voice": settings.voice_for(storyboard.language),
        "speaking_rate": settings.speaking_rate_for(storyboard.language),
        "tts": settings.section("tts"),
        "render": settings.section("render"),
    }


def build_fingerprint(storyboard: Storyboard, settings: Settings) -> str:
    return digest_json(build_payload(storyboard, settings))[:24]


def require_asset_approval(settings: Settings, build_hash: str) -> None:
    manifest_path = settings.project_root / "assets/mascot/rig/v2/manifest.json"
    if not manifest_path.exists():
        raise ValueError("Production mascot exports are missing")
    manifest = json.loads(manifest_path.read_text())
    approvals_path = settings.project_root / "catalog/creative-approvals.json"
    approvals = json.loads(approvals_path.read_text()) if approvals_path.exists() else {}
    manifest_hash = digest_json(content_only(manifest))
    if build_hash not in approvals.get("builds", []) or manifest_hash not in approvals.get(
        "mascots", []
    ):
        raise ValueError("Exact build and mascot versions require explicit owner approval")


def rendered_identity(
    storyboard: Storyboard, settings: Settings, audio: Path, timings: dict
) -> dict:
    """Seal the exact measured output, excluding machine paths and review state."""
    return {
        "inputs": build_payload(storyboard, settings),
        "narration_sha256": sha256(audio),
        "timing": content_only(timings),
    }


def verify_rendered_identity(storyboard, settings, audio, timings, saved_payload, fingerprint):
    current = rendered_identity(storyboard, settings, audio, timings)
    if current != saved_payload or digest_json(current)[:24] != fingerprint:
        raise ValueError(
            "Stale review package: current pixel/audio inputs differ from sealed build"
        )
    return current
