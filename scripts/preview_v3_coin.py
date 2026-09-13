"""Still-frame gate for the German coin template. No encode, no provider call."""

from __future__ import annotations

from PIL import Image, ImageDraw

from erklaerbaer.config import load_settings
from erklaerbaer.episode import synthetic_timing
from erklaerbaer.mechanisms import beat_at
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, school_font

BOARD = "storyboards/v3/springende-muenze/de-DE/0d6d2f1d3eb3b75d.json"
SAMPLES = 6
INK = "#344744"


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    board = Storyboard.model_validate_json((root / BOARD).read_text())
    timing = synthetic_timing(board, min_segment_seconds=3.0)
    renderer = PaperCutRenderer(settings)
    out = root / "build/v3/coin-preview"
    out.mkdir(parents=True, exist_ok=True)
    cell = (472, 266)

    for index, scene in enumerate(board.scenes):
        duration = timing["scene_durations"][index]
        started = sum(timing["scene_durations"][:index])
        moments = [duration * (i + 0.5) / SAMPLES for i in range(SAMPLES)]
        sheet = Image.new("RGB", (cell[0] * SAMPLES + 24, cell[1] + 120), "#f6f1e4")
        draw = ImageDraw.Draw(sheet)
        draw.text(
            (14, 18),
            f"{scene.scene_id}  {scene.shot.framing}",
            font=school_font(38),
            fill=INK,
        )
        for column, seconds in enumerate(moments):
            frame = renderer.render_frame(
                board,
                scene,
                progress=seconds / duration,
                scene_seconds=seconds,
                global_seconds=started + seconds,
                segments=timing["segments"],
            )
            state = beat_at(scene, seconds, list(timing["segments"]))
            box = (12 + column * cell[0], 68)
            sheet.paste(frame.convert("RGB").resize(cell, Image.Resampling.LANCZOS), box)
            draw.text(
                (box[0] + 4, box[1] + cell[1] + 6),
                f"{seconds:.1f}s  {state.action}",
                font=school_font(24),
                fill=INK,
            )
        sheet.save(out / f"{scene.scene_id}.jpg", quality=90)
        print(out / f"{scene.scene_id}.jpg")


if __name__ == "__main__":
    main()
