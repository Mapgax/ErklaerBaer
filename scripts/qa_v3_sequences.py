"""Sample every distinct sequence at several moments and lay the frames out for inspection.

A scene changes composition on a beat boundary, so each beat is sampled separately. The
point is to look at overlaps that only appear at particular phases of a motion, which a
single frame per scene will always miss.
"""

from __future__ import annotations

import json

from PIL import Image, ImageDraw

from erklaerbaer.config import load_settings
from erklaerbaer.mechanisms import beat_at
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, school_font

EPISODE = "88b41b6568bd1dbc709bcd66"
COIN = "7b4cd586ca92a616912625f8"
SAMPLES = 6
INK = "#344744"


def beat_windows(scene, timings, duration):
    """Start and end of each beat, so a sequence is sampled inside its own composition."""
    starts = sorted(
        {
            t["scene_start"]
            for t in timings
            if t["scene_id"] == scene.scene_id
            and t["segment_id"] in {b.segment_id for b in scene.mechanism.beats}
        }
    )
    edges = [*starts, duration]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    import sys

    folder = root / (
        f"artifacts/review-v3/coin/{COIN}"
        if "--coin" in sys.argv
        else f"artifacts/review-v3/guitar/{EPISODE}"
    )
    board = Storyboard.model_validate_json((folder / "storyboard.json").read_text())
    timing = json.loads((folder / "narration.timing.json").read_text())
    renderer = PaperCutRenderer(settings)
    out = root / ("build/v3/coin-sequence-qa" if "--coin" in sys.argv else "build/v3/sequence-qa")
    out.mkdir(parents=True, exist_ok=True)
    cell = (472, 266)

    for index, scene in enumerate(board.scenes):
        duration = timing["scene_durations"][index]
        started = sum(timing["scene_durations"][:index])
        windows = beat_windows(scene, timing["segments"], duration)
        rows = []
        for begin, end in windows:
            moments = [begin + (end - begin) * (i + 0.5) / SAMPLES for i in range(SAMPLES)]
            frames = []
            for seconds in moments:
                frame = renderer.render_frame(
                    board,
                    scene,
                    progress=seconds / duration,
                    scene_seconds=seconds,
                    global_seconds=started + seconds,
                    segments=timing["segments"],
                )
                state = beat_at(scene, seconds, list(timing["segments"]))
                frames.append((f"{seconds:.1f}s  {state.action}", frame))
            rows.append(frames)

        sheet = Image.new(
            "RGB", (cell[0] * SAMPLES + 24, (cell[1] + 44) * len(rows) + 76), "#f6f1e4"
        )
        draw = ImageDraw.Draw(sheet)
        draw.text(
            (14, 18), f"{scene.scene_id}  {scene.shot.framing}", font=school_font(38), fill=INK
        )
        for row, frames in enumerate(rows):
            for column, (caption, frame) in enumerate(frames):
                box = (12 + column * cell[0], 68 + row * (cell[1] + 44))
                sheet.paste(frame.convert("RGB").resize(cell, Image.Resampling.LANCZOS), box)
                draw.text(
                    (box[0] + 4, box[1] + cell[1] + 6), caption, font=school_font(24), fill=INK
                )
        sheet.save(out / f"{scene.scene_id}.jpg", quality=90)
        print(out / f"{scene.scene_id}.jpg")


if __name__ == "__main__":
    main()
