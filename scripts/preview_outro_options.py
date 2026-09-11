"""Still-frame options for a reusable outro. No encode, no provider call.

Each option is drawn at five moments of a four-second close, on the same backdrop and with
the same mascot library the intro uses, so what is compared is the idea and not the polish.
"""

from __future__ import annotations

import json

from PIL import Image, ImageDraw

from erklaerbaer.config import load_settings
from erklaerbaer.mascot_library import MascotLibrary, rig_root
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, _font, school_font

DURATION = 4.0
MOMENTS = (0.35, 1.1, 1.9, 2.7, 3.6)
INK = "#344744"
TEAL = "#34877f"
CORAL = "#d68462"
CREAM = "#fffcf3"
FAREWELL = {"nl-NL": "Tot ziens!", "de-DE": "Bis bald!"}
NEXT_QUESTION = {"nl-NL": "Tot de volgende vraag.", "de-DE": "Bis zur nächsten Frage."}


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def faded(layer, opacity):
    if opacity >= 1.0:
        return layer
    layer.putalpha(layer.getchannel("A").point(lambda a: round(a * max(0.0, opacity))))
    return layer


def close_out(seconds):
    """Everything fades together at the end, as the intro does at its start."""
    return ease(seconds / 0.4) * (1 - ease((seconds - (DURATION - 0.9)) / 0.8))


def dots(draw):
    draw.ellipse((1620, 175, 1670, 225), fill=TEAL)
    draw.ellipse((1690, 200, 1720, 230), fill=CORAL)


def option_bookend(canvas, seconds, library, language):
    """Mirror of the intro: the same oval and wordmark, with a raised paw and a farewell."""
    layer = Image.new("RGBA", canvas.size)
    d = ImageDraw.Draw(layer)
    d.ellipse((105, 120, 790, 940), fill=CREAM)
    dots(d)
    bear = library.frame("aha", min(1.75, seconds * 0.9), 735).copy()
    layer.alpha_composite(faded(bear, ease((seconds - 0.2) / 0.8)), (180, 150))
    words = Image.new("RGBA", canvas.size)
    wd = ImageDraw.Draw(words)
    wd.text((805, 335), "ErklaerBaer", font=_font(112, bold=True), fill=INK)
    layer.alpha_composite(faded(words, ease((seconds - 0.9) / 0.8)))
    bye = Image.new("RGBA", canvas.size)
    bd = ImageDraw.Draw(bye)
    bd.text(
        (810, 500),
        FAREWELL[language],
        font=school_font(84),
        fill=TEAL,
        stroke_width=1,
        stroke_fill=TEAL,
    )
    bd.line((812, 640, 1090, 640), fill=CORAL, width=5)
    layer.alpha_composite(faded(bye, ease((seconds - 1.8) / 0.8)))
    canvas.alpha_composite(faded(layer, close_out(seconds)))


def option_magnifier(canvas, seconds, library, language):
    """The brand prop closes the episode: the lens grows until it is the whole card."""
    layer = Image.new("RGBA", canvas.size)
    d = ImageDraw.Draw(layer)
    dots(d)
    grow = ease((seconds - 0.8) / 1.6)
    bear = library.frame("neutral", seconds, 660).copy()
    # The bear hands the frame to its own lens and leaves, so no paw is left sticking out.
    handover = ease((seconds - 0.1) / 0.6) * (1 - ease(grow * 1.5))
    layer.alpha_composite(faded(bear, handover), (250, 300))
    cx = 700.0 + (960 - 700.0) * grow
    cy = 430.0 + (540 - 430.0) * grow
    radius = 74 + grow * 356
    lens = Image.new("RGBA", canvas.size)
    ld = ImageDraw.Draw(lens)
    ld.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=CREAM,
        outline=TEAL,
        width=round(10 + 4 * grow),
    )
    layer.alpha_composite(faded(lens, ease((seconds - 0.7) / 0.5)))
    words = Image.new("RGBA", canvas.size)
    wd = ImageDraw.Draw(words)
    font = _font(104, bold=True)
    width = wd.textlength("ErklaerBaer", font=font)
    wd.text(((1920 - width) / 2, 462), "ErklaerBaer", font=font, fill=INK)
    tag = FAREWELL[language]
    small = school_font(70)
    wd.text(
        ((1920 - wd.textlength(tag, font=small)) / 2, 598),
        tag,
        font=small,
        fill=TEAL,
        stroke_width=1,
        stroke_fill=TEAL,
    )
    layer.alpha_composite(faded(words, ease((seconds - 2.1) / 0.7)))
    canvas.alpha_composite(faded(layer, close_out(seconds)))


def option_question(canvas, seconds, library, language):
    """A hand-off to the next episode, promising a question rather than a subject."""
    layer = Image.new("RGBA", canvas.size)
    d = ImageDraw.Draw(layer)
    d.ellipse((105, 120, 790, 940), fill=CREAM)
    dots(d)
    bear = library.frame("think", min(2.45, 0.6 + seconds * 0.7), 735).copy()
    layer.alpha_composite(faded(bear, ease((seconds - 0.2) / 0.8)), (180, 150))
    marks = Image.new("RGBA", canvas.size)
    md = ImageDraw.Draw(marks)
    for index in range(3):
        appear = ease((seconds - 1.0 - index * 0.35) / 0.5)
        r = 26 * appear
        if r < 1:
            continue
        x = 900 + index * 96
        md.ellipse((x - r, 430 - r, x + r, 430 + r), fill=TEAL if index < 2 else CORAL)
    layer.alpha_composite(marks)
    words = Image.new("RGBA", canvas.size)
    wd = ImageDraw.Draw(words)
    wd.text(
        (830, 520),
        NEXT_QUESTION[language],
        font=school_font(72),
        fill=INK,
        stroke_width=1,
        stroke_fill=INK,
    )
    wd.text((830, 640), "ErklaerBaer", font=_font(72, bold=True), fill=TEAL)
    layer.alpha_composite(faded(words, ease((seconds - 2.0) / 0.8)))
    canvas.alpha_composite(faded(layer, close_out(seconds)))


OPTIONS = (
    ("A  book-end: same card, raised paw, farewell", option_bookend),
    ("B  magnifier close: the lens becomes the card", option_magnifier),
    ("C  hand-off: three dots and the next question", option_question),
)


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    episode = root / "artifacts/review-v3/guitar/91e84166ea5e825f5708be6d"
    storyboard = Storyboard.model_validate(json.loads((episode / "storyboard.json").read_text()))
    backdrop = PaperCutRenderer(settings).render_background(storyboard, progress=0)
    library = MascotLibrary(rig_root(root))
    out = root / "build/v3/outro-options"
    out.mkdir(parents=True, exist_ok=True)
    cell = (600, 338)
    gap = 16

    phone = []
    for letter, (name, drawer) in zip("abc", OPTIONS, strict=True):
        sheet = Image.new("RGB", (cell[0] * 3 + gap * 4, (cell[1] + 58) * 2 + 110), "#f6f1e4")
        d = ImageDraw.Draw(sheet)
        d.text((gap + 4, 24), name, font=school_font(44), fill=INK)
        for index, seconds in enumerate(MOMENTS):
            canvas = backdrop.copy().convert("RGBA")
            drawer(canvas, seconds, library, "nl-NL")
            box = (gap + index % 3 * (cell[0] + gap), 100 + index // 3 * (cell[1] + 58))
            sheet.paste(canvas.convert("RGB").resize(cell, Image.Resampling.LANCZOS), box)
            d.text(
                (box[0] + 4, box[1] + cell[1] + 10),
                f"{seconds:.1f} s",
                font=school_font(30),
                fill=INK,
            )
            if index == 3:
                phone.append((name.split(":")[0], canvas.convert("RGB")))
        sheet.save(out / f"option-{letter}.jpg", quality=92)
        print(out / f"option-{letter}.jpg")

    width = 420
    strip = Image.new("RGB", (width * 3 + 40, round(width * 9 / 16) + 70), "#f6f1e4")
    sd = ImageDraw.Draw(strip)
    for index, (name, image) in enumerate(phone):
        x = 10 + index * (width + 10)
        strip.paste(image.resize((width, round(width * 9 / 16))), (x, 56))
        sd.text((x + 4, 14), name, font=school_font(30), fill=INK)
    strip.save(out / "phone.jpg", quality=92)
    print(out / "phone.jpg")


if __name__ == "__main__":
    main()
