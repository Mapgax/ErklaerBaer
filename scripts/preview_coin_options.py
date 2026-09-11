"""Design options for the German coin episode. No encode, no provider call.

Three sheets: the bottle and its lid, how pressure is shown, and how the cold start is
shown. Every option is drawn with the same gas, so what is being compared is the design.
"""

from __future__ import annotations

import json
import math

from PIL import Image, ImageDraw, ImageFilter

from erklaerbaer.collage_coin import (
    CREAM,
    GLASS,
    GLASS_FILL,
    METAL,
    METAL_EDGE,
    WARM,
    coin_art,
)
from erklaerbaer.collage_guitar import CORAL, INK, TEAL
from erklaerbaer.config import load_settings
from erklaerbaer.gas import positions
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, school_font

PARTICLE_RADIUS = 11
COUNT = 46

# Three silhouettes, all the same interior volume so the gas reads the same in each.
BOTTLES = {
    "1  Weithalsglas": (
        (930, 360),
        (1110, 360),
        (1290, 470),
        (1290, 940),
        (1230, 1000),
        (810, 1000),
        (750, 940),
        (750, 470),
    ),
    "2  Flasche mit kurzem Hals": (
        (952, 300),
        (1088, 300),
        (1088, 396),
        (1288, 520),
        (1288, 934),
        (1226, 1000),
        (814, 1000),
        (752, 934),
        (752, 520),
        (952, 396),
    ),
    "3  Schlanke Flasche": (
        (964, 258),
        (1076, 258),
        (1076, 430),
        (1256, 566),
        (1256, 928),
        (1200, 1000),
        (840, 1000),
        (784, 928),
        (784, 566),
        (964, 430),
    ),
}


def mouth_of(outline):
    """The opening is the topmost edge; the lid rests on it."""
    top = min(p[1] for p in outline)
    xs = sorted(p[0] for p in outline if abs(p[1] - top) < 1)
    return xs[0], xs[-1], top


def draw_bottle(stage, outline, *, warm=0.0, frost=0.0, tint=0.0):
    glass = Image.new("RGBA", stage.size)
    d = ImageDraw.Draw(glass)
    fill = GLASS_FILL
    if tint:
        fill = "#dce9ee"
    d.polygon(outline, fill=fill)
    d.line([*outline, outline[0]], fill=GLASS, width=15, joint="curve")
    left = min(p[0] for p in outline)
    top = min(p[1] for p in outline)
    bottom = max(p[1] for p in outline)
    d.line([(left + 62, top + 240), (left + 62, bottom - 120)], fill=CREAM, width=13)
    stage.alpha_composite(glass)
    if warm > 0.01:
        glow = Image.new("RGBA", stage.size)
        g = ImageDraw.Draw(glow)
        # Warmth sits in the side walls, where the hands are, and not in a pool on the floor.
        for x in (left + 10, max(p[0] for p in outline) - 10):
            g.line([(x, top + 300), (x, bottom - 110)], fill=WARM, width=round(14 + 14 * warm))
        glow.putalpha(glow.getchannel("A").point(lambda a: round(a * 0.7 * warm)))
        stage.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    if frost > 0.01:
        crystals = Image.new("RGBA", stage.size)
        c = ImageDraw.Draw(crystals)
        for index in range(26):
            angle = index * 2.399
            x = left + 70 + (index * 137) % 420
            y = bottom - 60 - (index * 83) % 250
            r = 5 + (index % 3) * 4
            for step in range(3):
                a = angle + step * math.pi / 3
                c.line(
                    [
                        (x - math.cos(a) * r, y - math.sin(a) * r),
                        (x + math.cos(a) * r, y + math.sin(a) * r),
                    ],
                    fill="#ffffff",
                    width=3,
                )
        crystals.putalpha(crystals.getchannel("A").point(lambda a: round(a * 0.85 * frost)))
        stage.alpha_composite(crystals)


def draw_lid(stage, outline, style, *, lift=0.0):
    left, right, top = mouth_of(outline)
    cx = (left + right) / 2
    width = (right - left) * 1.22
    if style == "flach":
        art = coin_art(width, width * 0.26)
        stage.alpha_composite(
            art, (round(cx - art.width / 2), round(top - art.height * 0.55 - lift))
        )
        return
    # A struck disc with a visible edge: the face on top, a milled band below it.
    height = width * 0.30
    thickness = width * 0.085
    art = Image.new("RGBA", (round(width) + 4, round(height + thickness) + 4))
    d = ImageDraw.Draw(art)
    d.ellipse((2, 2 + thickness, width, height + thickness), fill=METAL_EDGE)
    d.rectangle((2, 2 + height / 2, width, height / 2 + thickness), fill=METAL_EDGE)
    for step in range(0, round(width), 13):
        d.line(
            [(2 + step, 2 + height / 2), (2 + step, height / 2 + thickness)],
            fill="#6f6448",
            width=3,
        )
    face = coin_art(width - 2, height)
    art.alpha_composite(face, (2, 2))
    d.ellipse((2, 2, width, height), outline=METAL, width=3)
    stage.alpha_composite(art, (round(cx - art.width / 2), round(top - height * 0.55 - lift)))


def draw_gas(stage, outline, distance, *, halo=0.0, radius=PARTICLE_RADIUS):
    points = positions(outline, distance, count=COUNT, seed=7, margin=15 + radius)
    if halo > 0:
        aura = Image.new("RGBA", stage.size)
        a = ImageDraw.Draw(aura)
        reach = radius * (2.0 + 1.6 * halo)
        for x, y in points:
            a.ellipse((x - reach, y - reach, x + reach, y + reach), fill=TEAL)
        aura.putalpha(aura.getchannel("A").point(lambda v: round(v * 0.16)))
        stage.alpha_composite(aura.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(stage)
    for x, y in points:
        d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=TEAL)
    return points


def push_arrows(stage, outline, points, *, warm):
    """Every arrow marks a particle actually arriving at the lid, so the count is the cause."""
    left, right, top = mouth_of(outline)
    d = ImageDraw.Draw(stage)
    for x, y in points:
        if left <= x <= right and 0 < y - top < 120:
            tip = top + 16
            d.line([(x, y - 14), (x, tip)], fill=CORAL, width=5)
            d.polygon([(x, tip - 2), (x - 9, tip + 14), (x + 9, tip + 14)], fill=CORAL)
    label(d, f"Stöße auf den Deckel: {'viele' if warm else 'wenige'}", (120, 880), 40, CORAL)


def label(draw, text, xy, size, fill=INK):
    draw.text(xy, text, font=school_font(size), fill=fill, stroke_width=1, stroke_fill=fill)


def sheet(title, tiles, out, columns=3, cell=(600, 338)):
    gap = 16
    rows = (len(tiles) + columns - 1) // columns
    image = Image.new(
        "RGB", (cell[0] * columns + gap * (columns + 1), (cell[1] + 58) * rows + 110), "#f6f1e4"
    )
    d = ImageDraw.Draw(image)
    d.text((gap + 4, 24), title, font=school_font(44), fill=INK)
    for index, (caption, frame) in enumerate(tiles):
        box = (gap + index % columns * (cell[0] + gap), 100 + index // columns * (cell[1] + 58))
        image.paste(frame.convert("RGB").resize(cell, Image.Resampling.LANCZOS), box)
        d.text((box[0] + 4, box[1] + cell[1] + 10), caption, font=school_font(28), fill=INK)
    image.save(out, quality=92)
    print(out)


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    board = Storyboard.model_validate(
        json.loads(
            (root / "storyboards/v3/springende-muenze/de-DE/0d6d2f1d3eb3b75d.json").read_text()
        )
    )
    backdrop = PaperCutRenderer(settings).render_background(board, progress=0)
    out = root / "build/v3/coin-options"
    out.mkdir(parents=True, exist_ok=True)

    tiles = []
    for name, outline in BOTTLES.items():
        for style in ("flach", "gepraegt"):
            stage = backdrop.copy().convert("RGBA")
            draw_bottle(stage, outline, warm=0.5)
            draw_gas(stage, outline, 900.0)
            draw_lid(stage, outline, style)
            tiles.append((f"{name} / Deckel {style}", stage))
    sheet("Flasche und Deckel", tiles, out / "1-flasche.jpg", columns=2)

    outline = BOTTLES["2  Flasche mit kurzem Hals"]
    pressure = []
    for caption, halo, arrows, warm in (
        ("A  Stoßpfeile, kalt", 0.0, True, False),
        ("A  Stoßpfeile, warm", 0.0, True, True),
        ("B  Platzbedarf, kalt", 0.25, False, False),
        ("B  Platzbedarf, warm", 1.0, False, True),
    ):
        stage = backdrop.copy().convert("RGBA")
        draw_bottle(stage, outline, warm=0.8 if warm else 0.0)
        points = draw_gas(stage, outline, 2400.0 if warm else 700.0, halo=halo)
        draw_lid(stage, outline, "gepraegt")
        if arrows:
            push_arrows(stage, outline, points, warm=warm)
        pressure.append((caption, stage))
    sheet("Druck zeigen", pressure, out / "2-druck.jpg", columns=2)

    cold = []
    for caption, frost, tint in (
        ("1  Reif am Boden", 1.0, 0.0),
        ("2  kühl getöntes Glas", 0.0, 1.0),
        ("3  beides", 1.0, 1.0),
    ):
        stage = backdrop.copy().convert("RGBA")
        draw_bottle(stage, outline, frost=frost, tint=tint)
        draw_gas(stage, outline, 500.0)
        draw_lid(stage, outline, "gepraegt")
        cold.append((caption, stage))
    sheet("Kalte Flasche zeigen", cold, out / "3-kalt.jpg")


if __name__ == "__main__":
    main()
