from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from erklaerbaer.mascot_qa import inspect_library

ACTIONS = ("neutral", "lift", "explain", "think", "surprise", "aha")


def _write_library(root: Path, *, low_alpha_action: str | None = None) -> None:
    manifest = {"dimensions": [600, 800], "fps": 30, "actions": {}}
    for action_index, action in enumerate(ACTIONS):
        entries = []
        for frame_index in range(2):
            image = Image.new("RGBA", (600, 800), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            if action == low_alpha_action:
                box = (20, 20, 40, 40)
            else:
                offset = 0 if action == "neutral" else action_index * 12 + frame_index * 8
                box = (100 + offset, 150, 350 + offset, 500)
            color_frame = 0 if action == "neutral" else frame_index
            color = (70 + action_index * 25, 90, 120 + color_frame * 60, 255)
            draw.rectangle(box, fill=color)
            path = root / "frames" / action / f"{frame_index:04d}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path)
            entries.append(
                {
                    "file": str(path.relative_to(root)),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        manifest["actions"][action] = {
            "duration": 1.0,
            "behavior": "loop" if action == "neutral" else "play-once-hold-last",
            "loop": action == "neutral",
            "frames": entries,
        }
    (root / "manifest.json").write_text(json.dumps(manifest))


def test_inspect_library_accepts_distinct_transparent_actions(tmp_path: Path) -> None:
    _write_library(tmp_path)

    report = inspect_library(tmp_path)

    assert report["passed"] is True
    assert report["failures"] == []
    assert report["actions"]["neutral"]["loop_seam_mean_error"] == 0


def test_inspect_library_rejects_low_alpha_coverage(tmp_path: Path) -> None:
    _write_library(tmp_path, low_alpha_action="surprise")

    report = inspect_library(tmp_path)

    assert report["passed"] is False
    assert any("surprise: frame alpha coverage drops" in failure for failure in report["failures"])


def test_inspect_library_rejects_action_start_identical_to_neutral(tmp_path: Path) -> None:
    _write_library(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    neutral_path = tmp_path / manifest["actions"]["neutral"]["frames"][0]["file"]
    lift_entry = manifest["actions"]["lift"]["frames"][0]
    lift_path = tmp_path / lift_entry["file"]
    lift_path.write_bytes(neutral_path.read_bytes())
    lift_entry["sha256"] = hashlib.sha256(lift_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))

    report = inspect_library(tmp_path)

    assert report["passed"] is False
    assert "lift: action start is not distinct from neutral" in report["failures"]
