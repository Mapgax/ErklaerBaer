"""Reject stale or tampered local review bundles; never grant creative approval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_review_package import _validate_srt

from erklaerbaer.build_identity import sha256, verify_rendered_identity
from erklaerbaer.config import load_settings
from erklaerbaer.media import validate_media
from erklaerbaer.models import Storyboard
from erklaerbaer.science_review import validate_science_review


def validate(folder: Path):
    settings = load_settings()
    board = Storyboard.model_validate_json((folder / "storyboard.json").read_text())
    timings = json.loads((folder / "narration.timing.json").read_text())
    payload = json.loads((folder / "build-identity.json").read_text())
    validate_science_review(board, settings)
    verify_rendered_identity(
        board, settings, folder / "narration.wav", timings, payload, folder.name
    )
    for line in (folder / "checksums.sha256").read_text().splitlines():
        expected, name = line.split("  ", 1)
        path = (folder / name).resolve()
        if not path.is_relative_to(folder.resolve()) or sha256(path) != expected:
            raise ValueError("Review bundle checksum mismatch")
    media = validate_media(folder / "video.mp4", settings)
    captions = _validate_srt(folder / "captions.srt", media.probe.duration_seconds)
    return {
        "build_hash": folder.name,
        "technical_pass": not media.warnings,
        "captions": captions,
        "owner_approved": False,
        "creative_gate_complete": False,
        "limitations": [
            "Prop Rive source/runtime pending",
            "Full-video listening and owner creative review pending",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    report = validate(args.folder)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
