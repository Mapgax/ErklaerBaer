"""Still-frame gate for the radial air field. No encode, no provider call.

Renders the introduction beat and the two air shots at measured moments, at full size and
at the phone width that decides whether a mark reads.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from erklaerbaer.config import load_settings
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, school_font

EPISODE = "cedfada8807f70f3fe6b4a2c"
MOMENTS = {
    "scene-3": (5.0, 11.8, 13.6, 16.0, 20.0),
    "scene-4": (0.4, 1.6, 3.2, 6.0, 14.5),
    "scene-5": (0.5, 1.2, 2.6, 4.0, 7.0),
}
PHONE_WIDTH = 420
INK = "#344744"


def sheet(frames, title, out: Path, cell=(600, 338)):
    gap = 16
    image = Image.new("RGB", (cell[0] * 3 + gap * 4, (cell[1] + 58) * 2 + 110), "#f6f1e4")
    d = ImageDraw.Draw(image)
    d.text((gap + 4, 24), title, font=school_font(44), fill=INK)
    small = school_font(30)
    for index, (caption, frame) in enumerate(frames):
        box = (gap + index % 3 * (cell[0] + gap), 100 + index // 3 * (cell[1] + 58))
        image.paste(frame.convert("RGB").resize(cell, Image.Resampling.LANCZOS), box)
        d.text((box[0] + 4, box[1] + cell[1] + 10), caption, font=small, fill=INK)
    image.save(out, quality=92)
    return out


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    board = Storyboard.model_validate_json(
        (root / "storyboards/v3/karton-gitarre/nl-NL/7511ac9042e30f1e.json").read_text()
    )
    timing = json.loads(
        (root / "artifacts/review-v3/guitar" / EPISODE / "narration.timing.json").read_text()
    )
    renderer = PaperCutRenderer(settings)
    out = root / "build/v3/air-preview"
    out.mkdir(parents=True, exist_ok=True)

    phone = []
    for scene in board.scenes:
        if scene.scene_id not in MOMENTS:
            continue
        index = board.scenes.index(scene)
        started = sum(timing["scene_durations"][:index])
        frames = []
        for seconds in MOMENTS[scene.scene_id]:
            frame = renderer.render_frame(
                board,
                scene,
                progress=seconds / timing["scene_durations"][index],
                scene_seconds=seconds,
                global_seconds=started + seconds,
                segments=timing["segments"],
            )
            frame.save(out / f"{scene.scene_id}-{seconds:04.1f}s.png")
            frames.append((f"{seconds:.1f} s", frame))
        sheet(frames, f"{scene.scene_id}  {scene.shot.framing}", out / f"{scene.scene_id}.jpg")
        phone.append((scene.scene_id, frames[3][1]))

    strip = Image.new(
        "RGB", (PHONE_WIDTH * len(phone) + 40, round(PHONE_WIDTH * 9 / 16) + 70), "#f6f1e4"
    )
    d = ImageDraw.Draw(strip)
    for index, (name, frame) in enumerate(phone):
        x = 10 + index * (PHONE_WIDTH + 10)
        strip.paste(
            frame.convert("RGB").resize((PHONE_WIDTH, round(PHONE_WIDTH * 9 / 16))), (x, 56)
        )
        d.text((x + 4, 14), name, font=school_font(30), fill=INK)
    strip.save(out / "phone.jpg", quality=92)
    print(out)


if __name__ == "__main__":
    main()
