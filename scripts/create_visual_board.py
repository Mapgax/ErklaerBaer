from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from erklaerbaer.models import Language
from erklaerbaer.renderer import PaperCutRenderer
from tests.factories import make_settings, sample_storyboard

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "pilots" / "visual_direction_board.png"


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    )
    selected = next((path for path in candidates if path.exists()), None)
    return ImageFont.truetype(selected, size) if selected else ImageFont.load_default(size=size)


def main() -> None:
    settings = make_settings(ROOT)
    renderer = PaperCutRenderer(settings, width=920, height=500, fps=10)
    specifications = [
        (Language.GERMAN, "kuechenchemie", 3, "DE  Küchenchemie"),
        (Language.DUTCH, "weltraum-physik", 1, "NL  Ruimte & fysica"),
        (Language.GERMAN, "natur-tiere", 2, "DE  Natur & Tiere"),
        (Language.DUTCH, "technik", 7, "NL  Techniek"),
    ]
    canvas = Image.new("RGB", (1920, 1080), (31, 78, 75))
    positions = ((27, 27), (973, 27), (27, 553), (973, 553))
    badge_font = font(25)
    for position, (language, category, scene_index, badge) in zip(
        positions, specifications, strict=True
    ):
        storyboard = sample_storyboard(language).model_copy(update={"category": category})
        scene = storyboard.scenes[scene_index]
        frame = renderer.render_frame(storyboard, scene, progress=0.58, mouth=0.32)
        draw = ImageDraw.Draw(frame)
        bounds = draw.textbbox((0, 0), badge, font=badge_font)
        badge_width = bounds[2] - bounds[0] + 32
        draw.rounded_rectangle((18, 440, 18 + badge_width, 482), radius=17, fill=(31, 78, 75))
        draw.text((34, 446), badge, font=badge_font, fill=(255, 252, 243))
        canvas.paste(frame, position)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
