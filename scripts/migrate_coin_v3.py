"""Carry the reviewed German coin script from schema 2 to schema 3.

Only presentation is added: a shot per scene, the speaker and delivery the v3 voices need,
and the mascot placement the v3 template expects. No narration text changes, so the science
review still covers the same words.
"""

from __future__ import annotations

import json

from erklaerbaer.config import load_settings
from erklaerbaer.models import Storyboard

# One composition per scene, and never the same one twice in a row.
FRAMINGS = (
    "establish",
    "micro",
    "heat",
    "pressure",
    "reaction",
    "lift",
    "reset",
    "recap",
)
# The bear opens the question and asks the prediction; the explanation scenes are his to
# stay out of, and the recap is where he lands the answer.
MASCOT = {
    1: {"visible": True, "action": "neutral", "height_fraction": 0.62},
    5: {"visible": True, "action": "think", "height_fraction": 0.65},
    8: {"visible": False, "action": "aha", "height_fraction": 0.65},
}
BEAR_SEGMENTS = {"scene-1-1", "scene-1-4", "scene-5-1"}


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    source = root / "storyboards/springende-muenze/de-DE/0d6d2f1d3eb3b75d.json"
    board = json.loads(source.read_text())
    board["schema_version"] = "3"
    board["template_version"] = "3"

    for index, scene in enumerate(board["scenes"], start=1):
        scene["shot"] = {
            "template_id": "coin-collage",
            "version": "3",
            "framing": FRAMINGS[index - 1],
            "asset_bundle": "coin-v3",
        }
        mascot = MASCOT.get(index, {"visible": False, "action": "neutral", "height_fraction": 0.65})
        scene["mascot"] = {**mascot, "placement": "left", "start_seconds": 0.0}
        for segment in scene["segments"]:
            bear = segment["segment_id"] in BEAR_SEGMENTS
            segment["speaker"] = "bear" if bear else "narrator"
            segment["delivery"] = "curious" if bear else "warm"

    target = root / "storyboards/v3/springende-muenze/de-DE/0d6d2f1d3eb3b75d.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    validated = Storyboard.model_validate(board)
    target.write_text(json.dumps(board, ensure_ascii=False, indent=2) + "\n")
    print(target)
    print("scenes:", len(validated.scenes))
    for scene in validated.scenes:
        print(f"  {scene.scene_id:9} {scene.shot.framing:10} mascot={scene.mascot.visible}")


if __name__ == "__main__":
    main()
