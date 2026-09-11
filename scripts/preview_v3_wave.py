"""Still-frame gate for the reworked air and ear shots. No encode, no provider call.

Renders the two shots at several measured moments and lays them beside the frames
decoded from the delivered build, at full size and at phone width.
"""

from __future__ import annotations

import json

from PIL import Image, ImageDraw

from erklaerbaer.config import load_settings
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, _font

DELIVERED = "cedfada8807f70f3fe6b4a2c"
# Scene 3's second beat opens the air window; its moments are offset by that beat's start.
MOMENTS = {
    "scene-3": (11.8, 12.5, 13.2, 14.4, 17.0),
    "scene-4": (0.4, 1.0, 1.9, 3.4, 6.0),
    "scene-5": (0.5, 1.2, 2.4, 3.6, 6.2),
}
PHONE_WIDTH = 400


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    board = Storyboard.model_validate_json(
        (root / "storyboards/v3/karton-gitarre/nl-NL/7511ac9042e30f1e.json").read_text()
    )
    episode = root / "artifacts/review-v3/guitar" / DELIVERED
    timing = json.loads((episode / "narration.timing.json").read_text())
    renderer = PaperCutRenderer(settings)
    out = root / "build/v3/wave-preview"
    out.mkdir(parents=True, exist_ok=True)
    label = _font(34, bold=True)

    for scene in board.scenes:
        if scene.scene_id not in MOMENTS:
            continue
        index = board.scenes.index(scene)
        started = sum(timing["scene_durations"][:index])
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

    for scene_id, old_name in (
        ("scene-3", "scene-3.png"),
        ("scene-4", "scene-4.png"),
        ("scene-5", "scene-5.png"),
    ):
        moments = MOMENTS[scene_id]
        columns = len(moments) + 1
        cell = (620, 349)
        sheet = Image.new("RGB", (cell[0] * 3, cell[1] * 2 + 96), "#f6f1e4")
        draw = ImageDraw.Draw(sheet)
        before = Image.open(root / "build/v3/mp4-qa" / DELIVERED / old_name).convert("RGB")
        tiles = [("delivered", before)] + [
            (f"new {seconds:.1f}s", Image.open(out / f"{scene_id}-{seconds:04.1f}s.png"))
            for seconds in moments
        ]
        for position, (caption, image) in enumerate(tiles[:6]):
            box = (position % 3 * cell[0], position // 3 * (cell[1] + 48) + 48)
            sheet.paste(image.convert("RGB").resize(cell, Image.Resampling.LANCZOS), box)
            draw.text((box[0] + 14, box[1] - 40), caption, font=label, fill="#344744")
        sheet.save(out / f"{scene_id}-comparison.jpg", quality=90)
        assert columns  # keeps the moment count meaningful in the layout above

        phone = Image.new(
            "RGB", (PHONE_WIDTH * 2 + 30, round(PHONE_WIDTH * 9 / 16) + 60), "#f6f1e4"
        )
        pd = ImageDraw.Draw(phone)
        for position, (caption, image) in enumerate([tiles[0], tiles[3 if len(tiles) > 3 else -1]]):
            size = (PHONE_WIDTH, round(PHONE_WIDTH * 9 / 16))
            phone.paste(
                image.convert("RGB").resize(size, Image.Resampling.LANCZOS),
                (position * (PHONE_WIDTH + 30), 50),
            )
            pd.text(
                (position * (PHONE_WIDTH + 30) + 6, 12),
                caption,
                font=_font(22, bold=True),
                fill="#344744",
            )
        phone.save(out / f"{scene_id}-phone.jpg", quality=92)

    print(out)


if __name__ == "__main__":
    main()
