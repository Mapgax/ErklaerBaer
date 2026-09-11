from PIL import Image, ImageDraw

from erklaerbaer.config import load_settings
from erklaerbaer.renderer import PaperCutRenderer
from erklaerbaer.storyboards import load_storyboard

settings = load_settings()
out = settings.project_root / "build/production-v2-review"
out.mkdir(parents=True, exist_ok=True)
renderer = PaperCutRenderer(settings, width=960, height=540)
for topic, lang in [
    ("springende-muenze", "de-DE"),
    ("karton-gitarre", "nl-NL"),
    ("krabbeltier-safari", "nl-NL"),
]:
    board = load_storyboard(
        next((settings.project_root / "storyboards" / topic / lang).glob("*.json"))
    )
    sheet = Image.new("RGB", (1920, 4 * 590), "white")
    for i, scene in enumerate(board.scenes):
        scene = scene.model_copy(deep=True)
        scene.mascot.visible = False
        frame = renderer.render_frame(board, scene, progress=0.6)
        x = (i % 2) * 960
        y = (i // 2) * 590
        sheet.paste(frame, (x, y))
        ImageDraw.Draw(sheet).text(
            (x + 30, y + 548),
            f"{i + 1}. {scene.primitive}: " + ", ".join(b.action for b in scene.mechanism.beats),
            fill="black",
        )
    sheet.save(out / f"{topic}-mechanisms.jpg")
    print(out / f"{topic}-mechanisms.jpg")
