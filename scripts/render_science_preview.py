"""Render a low-cost timing proof without requiring the pending mascot export."""

from __future__ import annotations

import argparse
import json

from erklaerbaer.config import load_settings
from erklaerbaer.renderer import PaperCutRenderer
from erklaerbaer.storyboards import load_storyboard


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("topic")
    parser.add_argument("language")
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root
    storyboard_path = next((root / "storyboards" / args.topic / args.language).glob("*.json"))
    storyboard = load_storyboard(storyboard_path)
    storyboard = storyboard.model_copy(
        update={
            "scenes": [
                scene.model_copy(
                    update={"mascot": scene.mascot.model_copy(update={"visible": False})}
                )
                for scene in storyboard.scenes
            ]
        }
    )
    review_root = root / "build" / "production-v2-review" / args.topic
    timing = json.loads((review_root / "narration.timing.json").read_text())
    renderer = PaperCutRenderer(settings, width=960, height=540, fps=10)
    output = review_root / "science-timing-preview.mp4"
    renderer.render_video(
        storyboard,
        timing["scene_durations"],
        output,
        audio_path=review_root / "narration.wav",
        segments=timing["segments"],
    )
    print(output)


if __name__ == "__main__":
    main()
