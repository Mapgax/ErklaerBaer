"""Still-frame gate for the falling-objects template. No encode, no provider call.

Timing is synthetic until speech exists, or measured when --timing names a real
narration.timing.json. Each scene is sampled evenly and again around every release, which is
where overlaps and landings happen.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

from erklaerbaer.collage_fall import FALL_SECONDS, release_time
from erklaerbaer.config import load_settings
from erklaerbaer.episode import synthetic_timing
from erklaerbaer.mechanisms import beat_at
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, school_font

BOARD = "storyboards/v3/fall-wettrennen/nl-NL/c120949aca72eba7.json"
SAMPLES = 6
INK = "#344744"


def moments_for(scene, duration, segments):
    moments = [duration * (i + 0.5) / SAMPLES for i in range(SAMPLES)]
    if any(beat.action == "release" for beat in scene.mechanism.beats):
        release = release_time(scene, segments)
        moments += [release + f * FALL_SECONDS for f in (0.05, 0.5, 0.9, 1.1)]
    return sorted(m for m in moments if 0 <= m < duration)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timing", type=Path)
    parser.add_argument("--out", default="build/v3/fall-preview")
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root
    board = Storyboard.model_validate_json((root / BOARD).read_text())
    timing = (
        json.loads(args.timing.read_text())
        if args.timing
        else synthetic_timing(board, min_segment_seconds=1.4)
    )
    renderer = PaperCutRenderer(settings)
    out = root / args.out
    out.mkdir(parents=True, exist_ok=True)
    cell = (480, 270)
    phone = []

    for index, scene in enumerate(board.scenes):
        duration = timing["scene_durations"][index]
        started = sum(timing["scene_durations"][:index])
        moments = moments_for(scene, duration, timing["segments"])
        columns = 5
        rows = (len(moments) + columns - 1) // columns
        sheet = Image.new("RGB", (cell[0] * columns + 24, (cell[1] + 40) * rows + 70), "#f6f1e4")
        draw = ImageDraw.Draw(sheet)
        draw.text(
            (14, 14), f"{scene.scene_id}  {scene.shot.framing}", font=school_font(38), fill=INK
        )
        for n, seconds in enumerate(moments):
            frame = renderer.render_frame(
                board,
                scene,
                progress=seconds / duration,
                scene_seconds=seconds,
                global_seconds=started + seconds,
                segments=timing["segments"],
            ).convert("RGB")
            if n == len(moments) // 2:
                frame.save(out / f"{scene.scene_id}-full.png")
                phone.append(frame.resize((390, 219), Image.Resampling.LANCZOS))
            state = beat_at(scene, seconds, list(timing["segments"]))
            box = (12 + (n % columns) * cell[0], 64 + (n // columns) * (cell[1] + 40))
            sheet.paste(frame.resize(cell, Image.Resampling.LANCZOS), box)
            draw.text(
                (box[0] + 4, box[1] + cell[1] + 4),
                f"{seconds:.2f}s  {state.action}",
                font=school_font(24),
                fill=INK,
            )
        sheet.save(out / f"{scene.scene_id}.jpg", quality=90)
        print(out / f"{scene.scene_id}.jpg", flush=True)
    strip = Image.new("RGB", (390 * 3 + 20, 229 * 3), "#ffffff")
    for n, frame in enumerate(phone):
        strip.paste(frame, (5 + (n % 3) * 395, 5 + (n // 3) * 229))
    strip.save(out / "phone-strip.png")


if __name__ == "__main__":
    main()
