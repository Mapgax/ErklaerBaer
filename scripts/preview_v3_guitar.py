"""Inspect the actual v3 renderer with cached measured timings, without provider calls."""

import json

from PIL import Image, ImageDraw

from erklaerbaer.config import load_settings
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer

s = load_settings()
root = s.project_root
b = Storyboard.model_validate_json(
    (root / "storyboards/v3/karton-gitarre/nl-NL/7511ac9042e30f1e.json").read_text()
)
timing = json.loads(
    (root / "artifacts/review-v2/pilots/karton-gitarre/narration.timing.json").read_text()
)
r = PaperCutRenderer(s)
out = root / "build/v3/frames"
out.mkdir(parents=True, exist_ok=True)
contact = Image.new("RGB", (1280, 4 * 390), "#f8efd8")
d = ImageDraw.Draw(contact)
for i, scene in enumerate(b.scenes):
    seconds = 5.0
    frame = r.render_frame(
        b,
        scene,
        progress=0.4,
        scene_seconds=seconds,
        global_seconds=sum(timing["scene_durations"][:i]) + seconds,
        segments=timing["segments"],
    )
    frame.save(out / f"{i + 1}.png")
    frame.thumbnail((640, 360))
    contact.paste(frame, (i % 2 * 640, i // 2 * 390 + 30))
    d.text((i % 2 * 640 + 20, i // 2 * 390 + 5), scene.shot.framing, fill="black")
contact.save(out / "contact.jpg")
print(out / "contact.jpg")
