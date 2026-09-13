"""Reusable paper bottle template: authored geometry, deterministic gas, measured beats.

All coordinates are in a stable 1920x1080 stage. Every geometry is derived from the view a
shot picks, so nothing drifts when a camera moves and no two consecutive scenes share a
composition. Particles move inside the drawn outline, not inside a rectangle that
approximates it, so none can appear in the shoulders or outside the glass.

Owner choices, 2026-09-11: a bottle with a short neck, a thick struck lid, warmth shown as
a glow in the side walls the hands touch, cold shown as a cool tint in the glass, and
pressure shown as a halo on each particle. The halo scales with how fast a particle moves,
so it says "this one pushes harder" rather than "this one needs more room", which would
contradict the script's own line that the bottle stays the same size.
"""

from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from . import gas
from .collage_guitar import CORAL, CREAM, INK, ROOT, TEAL, material, paste_prop
from .mascot_library import MascotLibrary, rig_root
from .renderer import school_font

GLASS = "#7f9c98"
GLASS_WARM = "#e8efe9"
GLASS_COLD = "#d3e3ee"
METAL = "#b9ac86"
METAL_EDGE = "#8a7d5c"
METAL_SIDE = "#6f6448"
WARM = "#d9724f"

# The bottle in its base view: straight body, sloped shoulders, a short neck for the lid.
BASE_OUTLINE = (
    (952.0, 300.0),
    (1088.0, 300.0),
    (1088.0, 396.0),
    (1288.0, 520.0),
    (1288.0, 934.0),
    (1226.0, 1000.0),
    (814.0, 1000.0),
    (752.0, 934.0),
    (752.0, 520.0),
    (952.0, 396.0),
)
WALL = 15.0
# Words live left of the bottle, above the line the hands occupy.
TEXT_X = 214.0
TEXT_ROWS = (298.0, 376.0, 454.0)
# Above the band the hands occupy in every view, so a close-up never hides it.
CAPTION_Y = 532.0
# Nothing a shot draws may reach the heading the renderer puts above this line.
HEADING_FLOOR = 262.0

PARTICLES = 46
PARTICLE_RADIUS = 11.0
BASE_SPEED = 118.0
WARM_BOOST = 1.05
SEED = 7

# One camera per framing, so a scene never repeats the one before it.
VIEWS = {
    "establish": (0.80, 1180.0, 690.0),
    "micro": (1.05, 1040.0, 700.0),
    "heat": (0.88, 1180.0, 700.0),
    "pressure": (1.25, 1060.0, 790.0),
    "reaction": (0.72, 1260.0, 690.0),
    "lift": (1.15, 1100.0, 780.0),
    "reset": (0.92, 1160.0, 700.0),
    "recap": (0.68, 1320.0, 690.0),
}


class View:
    """The bottle as one shot sees it. Everything else is measured from these numbers."""

    def __init__(self, framing="heat"):
        scale, centre_x, centre_y = VIEWS[framing]
        self.scale = scale
        base_cx = sum(p[0] for p in BASE_OUTLINE) / len(BASE_OUTLINE)
        base_cy = (min(p[1] for p in BASE_OUTLINE) + max(p[1] for p in BASE_OUTLINE)) / 2
        self.outline = tuple(
            (centre_x + (x - base_cx) * scale, centre_y + (y - base_cy) * scale)
            for x, y in BASE_OUTLINE
        )
        self.wall = WALL * scale
        self.radius = PARTICLE_RADIUS * scale
        top = min(p[1] for p in self.outline)
        rim = sorted(p[0] for p in self.outline if abs(p[1] - top) < 0.5)
        self.mouth = (rim[0], rim[-1], top)
        self.left = min(p[0] for p in self.outline)
        self.right = max(p[0] for p in self.outline)
        self.bottom = max(p[1] for p in self.outline)


def gas_points(view, distance):
    """Particle centres, kept far enough from the glass that no mark straddles the wall."""
    return gas.positions(
        view.outline,
        distance,
        count=PARTICLES,
        seed=SEED,
        margin=view.wall + view.radius,
    )


def travelled(seconds, warm=0.0):
    """Distance covered so far. Warming changes speed, never the number of particles."""
    return BASE_SPEED * max(0.0, seconds) * (1.0 + WARM_BOOST * warm)


def warmth(seconds, start, ramp):
    x = min(1.0, max(0.0, (seconds - start) / ramp))
    return x * x * (3 - 2 * x)


@lru_cache(maxsize=16)
def lid_art(width, height, thickness):
    """A struck disc with a visible milled edge, authored at the size it is shown."""
    width, height, thickness = round(width), round(height), round(thickness)
    art = Image.new("RGBA", (width + 4, height + thickness + 4))
    d = ImageDraw.Draw(art)
    d.ellipse((2, 2 + thickness, width, height + thickness), fill=METAL_EDGE)
    d.rectangle((2, 2 + height / 2, width, height / 2 + thickness), fill=METAL_EDGE)
    for step in range(0, width, max(6, round(width / 22))):
        d.line(
            [(2 + step, 2 + height / 2), (2 + step, height / 2 + thickness)],
            fill=METAL_SIDE,
            width=max(2, round(width / 90)),
        )
    face = ImageEnhance.Brightness(material("edge", width - 2, height)).enhance(1.5)
    mask = Image.new("L", (width - 2, height))
    ImageDraw.Draw(mask).ellipse((0, 0, width - 3, height - 1), fill=255)
    face.putalpha(mask)
    art.alpha_composite(face, (2, 2))
    d.ellipse((2, 2, width, height), outline=METAL, width=max(2, round(width / 55)))
    d.ellipse(
        (width * 0.17, 2 + height * 0.24, width * 0.83, height * 0.78),
        outline=METAL,
        width=max(2, round(width / 90)),
    )
    return art


def _blend(warm_hex, cold_hex, amount):
    warm_rgb = tuple(int(warm_hex[i : i + 2], 16) for i in (1, 3, 5))
    cold_rgb = tuple(int(cold_hex[i : i + 2], 16) for i in (1, 3, 5))
    return tuple(round(a + (b - a) * amount) for a, b in zip(warm_rgb, cold_rgb, strict=True))


def draw_bottle(view, stage, *, warm=0.0, cold=0.0):
    """The glass, its cool start, and the warmth the hands put into its side walls."""
    glass = Image.new("RGBA", stage.size)
    d = ImageDraw.Draw(glass)
    d.polygon(view.outline, fill=_blend(GLASS_WARM, GLASS_COLD, cold))
    d.line(
        [*view.outline, view.outline[0]],
        fill=GLASS,
        width=max(2, round(view.wall)),
        joint="curve",
    )
    d.line(
        [
            (view.left + 62 * view.scale, view.mouth[2] + 240 * view.scale),
            (view.left + 62 * view.scale, view.bottom - 120 * view.scale),
        ],
        fill=CREAM,
        width=max(2, round(13 * view.scale)),
    )
    stage.alpha_composite(glass)
    if warm <= 0.01:
        return
    glow = Image.new("RGBA", stage.size)
    g = ImageDraw.Draw(glow)
    # The warmth is in the walls the hands hold, not in a pool on the floor.
    for x in (view.left + 10 * view.scale, view.right - 10 * view.scale):
        g.line(
            [(x, view.mouth[2] + 300 * view.scale), (x, view.bottom - 110 * view.scale)],
            fill=WARM,
            width=max(3, round((14 + 14 * warm) * view.scale)),
        )
    glow.putalpha(glow.getchannel("A").point(lambda a: round(a * 0.7 * warm)))
    stage.alpha_composite(glow.filter(ImageFilter.GaussianBlur(max(2, round(10 * view.scale)))))


@lru_cache(maxsize=8)
def hand_art(height, mirrored):
    with Image.open(ROOT / "assets/library/hands/v3/hand.png") as source:
        art = source.convert("RGBA")
    width = round(art.width * height / art.height)
    art = art.resize((width, round(height)), Image.Resampling.LANCZOS)
    return art.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if mirrored else art


def draw_hands(view, stage, reach):
    """Paper hands closing on the glass. Their fingertips stop at the wall, never inside it."""
    if reach <= 0.01:
        return
    height = (view.bottom - view.mouth[2]) * 0.46
    middle = (view.mouth[2] + view.bottom) / 2 + 60 * view.scale
    for side in (-1, 1):
        art = hand_art(round(height), side > 0)
        wall = view.left if side < 0 else view.right
        gap = (1 - reach) * 130 * view.scale
        x = wall - art.width - gap if side < 0 else wall + gap
        # No drop shadow: beside the glass it read as a smear painted onto the bottle.
        paste_prop(stage, art, (x, middle - art.height / 2, art.width, art.height), shadow=False)


def draw_lid(view, stage, *, lift=0.0, tilt=0.0):
    left, right, top = view.mouth
    width = (right - left) * 1.28
    height = width * 0.30
    thickness = width * 0.11
    art = lid_art(width, height, thickness)
    if tilt:
        art = art.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=True)
    cx = (left + right) / 2
    paste_prop(stage, art, (cx - art.width / 2, top - height * 0.55 - lift, art.width, art.height))


def draw_gas(view, stage, points, *, halo=0.0, colour=TEAL):
    """Marks of one size, with a halo that grows with how hard a particle pushes."""
    if halo > 0:
        aura = Image.new("RGBA", stage.size)
        a = ImageDraw.Draw(aura)
        for (x, y), rate in zip(points, gas.speeds(PARTICLES, SEED), strict=True):
            reach = view.radius * (1.5 + 1.5 * halo * rate)
            a.ellipse((x - reach, y - reach, x + reach, y + reach), fill=colour)
        aura.putalpha(aura.getchannel("A").point(lambda v: round(v * 0.18)))
        stage.alpha_composite(aura.filter(ImageFilter.GaussianBlur(max(2, round(6 * view.scale)))))
    d = ImageDraw.Draw(stage)
    r = view.radius
    for x, y in points:
        d.ellipse((x - r, y - r, x + r, y + r), fill=colour)


def label(draw, text, xy, font, fill=INK):
    draw.text(xy, text, font=font, fill=fill, stroke_width=1, stroke_fill=fill)


def establish_shot(view, stage, seconds, action, *, small_font):
    """The cold bottle, the coin on it, and the hands that will do the warming."""
    cold = 1.0 if action == "observe" else max(0.0, 1.0 - seconds / 2.0)
    draw_bottle(view, stage, cold=cold)
    draw_gas(view, stage, gas_points(view, travelled(seconds)))
    reach = 0.0 if action == "observe" else min(1.0, max(0.0, (seconds - 0.2) / 0.9))
    draw_hands(view, stage, reach)
    lift = 0.0
    if action == "lift" and seconds > 0.3:
        lift = max(0.0, 16 * view.scale * math.sin(math.tau * 1.1 * seconds))
    draw_lid(view, stage, lift=lift)


def micro_shot(view, stage, seconds, *, small_font):
    """Name the particles, then let the collisions matter."""
    draw_bottle(view, stage, cold=0.85)
    draw_gas(view, stage, gas_points(view, travelled(seconds)))
    draw_lid(view, stage)
    d = ImageDraw.Draw(stage)
    label(d, "kalte Flasche", (TEXT_X, TEXT_ROWS[0]), small_font, fill=GLASS)
    if seconds > 0.7:
        label(d, "Luftteilchen", (TEXT_X, TEXT_ROWS[1]), small_font)
        label(d, "viel freier Raum dazwischen", (TEXT_X, TEXT_ROWS[2]), small_font, fill=TEAL)
    if seconds > 3.2:
        label(d, "Stösse gegen Wand und Münze", (TEXT_X, CAPTION_Y), small_font, fill=CORAL)


def heat_shot(view, stage, seconds, *, small_font):
    """Warmth enters the walls the hands hold, and then the particles move faster."""
    warm = warmth(seconds, 0.6, 2.2)
    draw_bottle(view, stage, warm=warm, cold=1.0 - warm)
    draw_hands(view, stage, 1.0)
    draw_gas(view, stage, gas_points(view, travelled(seconds, warm)), halo=warm)
    draw_lid(view, stage)
    d = ImageDraw.Draw(stage)
    label(d, "Wärme durch das Glas", (TEXT_X, TEXT_ROWS[0]), small_font, fill=WARM)
    if warm > 0.35:
        label(d, "gleich viele Teilchen, schneller", (TEXT_X, TEXT_ROWS[1]), small_font, fill=TEAL)
    label(d, "Stark vergrössert", (TEXT_X, CAPTION_Y), small_font)


def pressure_shot(view, stage, seconds, *, small_font):
    """The halo says how hard a particle pushes, and it grows with its speed."""
    draw_bottle(view, stage, warm=0.85)
    draw_hands(view, stage, 1.0)
    draw_gas(view, stage, gas_points(view, travelled(seconds, 1.0)), halo=1.0)
    draw_lid(view, stage)
    d = ImageDraw.Draw(stage)
    label(d, "jedes Teilchen drückt kräftiger", (TEXT_X, TEXT_ROWS[0]), small_font, fill=CORAL)
    label(
        d,
        "aussen drückt die Luft gleich weiter",
        (TEXT_X, TEXT_ROWS[1]),
        small_font,
        fill="#7f8f8a",
    )
    label(d, "Der Unterschied zählt", (TEXT_X, TEXT_ROWS[2]), small_font)
    label(d, "Stark vergrössert", (TEXT_X, CAPTION_Y), small_font)


def lift_shot(view, stage, seconds, *, small_font):
    """The lid rises and the air leaves through the opening it uncovers, not beside it."""
    opened = min(1.0, max(0.0, (seconds - 0.8) / 1.0))
    lift = 34 * view.scale * opened
    draw_bottle(view, stage, warm=0.9)
    draw_hands(view, stage, 1.0)
    draw_gas(view, stage, gas_points(view, travelled(seconds, 1.0)), halo=1.0)
    left, right, top = view.mouth
    cx = (left + right) / 2
    if opened > 0.05:
        # The stream starts inside the neck and rises through the gap under the lid.
        d = ImageDraw.Draw(stage)
        span = (right - left) * 0.62
        for index in range(7):
            phase = (seconds * 0.75 + index / 7) % 1.0
            x = cx + (index - 3) / 3 * span / 2
            y = top + 10 * view.scale - phase * 150 * view.scale * opened
            r = max(1.0, view.radius * (1 - phase * 0.55))
            d.ellipse((x - r, y - r, x + r, y + r), fill=TEAL)
    draw_lid(view, stage, lift=lift, tilt=-5 * opened)
    d = ImageDraw.Draw(stage)
    if opened > 0.15:
        label(d, "Spalt: Luft entweicht", (TEXT_X, TEXT_ROWS[0]), small_font, fill=TEAL)
    if opened > 0.6:
        label(d, "Druckunterschied sinkt", (TEXT_X, TEXT_ROWS[1]), small_font, fill=CORAL)
    label(d, "Stark vergrössert", (TEXT_X, CAPTION_Y), small_font)


def reset_shot(view, stage, seconds, *, small_font):
    """The lid falls back and the cycle can run again while the hands keep warming."""
    fall = max(0.0, 1.0 - min(1.0, seconds / 0.7))
    draw_bottle(view, stage, warm=0.75)
    draw_hands(view, stage, 1.0)
    draw_gas(view, stage, gas_points(view, travelled(seconds, 0.8)), halo=0.8)
    draw_lid(view, stage, lift=30 * view.scale * fall)
    d = ImageDraw.Draw(stage)
    label(d, "Münze fällt zurück", (TEXT_X, TEXT_ROWS[0]), small_font)
    if seconds > 2.0:
        label(d, "und es kann von vorn beginnen", (TEXT_X, TEXT_ROWS[1]), small_font, fill=TEAL)
    label(d, "Stark vergrössert", (TEXT_X, CAPTION_Y), small_font)


RECAP_STEPS = ("Wärme", "schnellere Teilchen", "mehr Druck", "Münze hebt sich", "Luft entweicht")
RECAP_BY_ACTION = {"heat": 1, "lift": 3, "vent": 4, "reset": 4}


def recap_shot(view, stage, seconds, action, *, small_font):
    """The steps arrive with the sentences that say them, not on a timer of their own."""
    draw_bottle(view, stage, warm=0.7)
    draw_hands(view, stage, 1.0)
    draw_gas(view, stage, gas_points(view, travelled(seconds, 0.7)), halo=0.7)
    step = RECAP_BY_ACTION.get(action, 0)
    draw_lid(view, stage, lift=26 * view.scale if action == "lift" else 0.0)
    d = ImageDraw.Draw(stage)
    for index, text in enumerate(RECAP_STEPS[: step + 1]):
        colour = CORAL if index == step else INK
        label(
            d, f"{index + 1}. {text}", (TEXT_X, TEXT_ROWS[0] + index * 78), small_font, fill=colour
        )


def draw(canvas, scene, seconds, state, *, font, small_font, segments=()):
    """Render one known semantic shot. No evaluated paths or generated code.

    Every template receives the measured `segments`; this one times its beats from `state`.
    """
    stage = Image.new("RGBA", (1920, 1080))
    framing = scene.shot.framing
    view = View(framing)
    if framing == "establish":
        establish_shot(view, stage, state.elapsed, state.action, small_font=small_font)
    elif framing == "micro":
        micro_shot(view, stage, seconds, small_font=small_font)
    elif framing == "heat":
        heat_shot(view, stage, seconds, small_font=small_font)
    elif framing == "pressure":
        pressure_shot(view, stage, seconds, small_font=small_font)
    elif framing == "reaction":
        # Quiet prediction hold; the bear gets the room and the bottle keeps its state.
        draw_bottle(view, stage, warm=0.8)
        draw_gas(view, stage, gas_points(view, travelled(seconds, 1.0)), halo=0.9)
        draw_lid(view, stage)
    elif framing == "lift":
        lift_shot(view, stage, seconds, small_font=small_font)
    elif framing == "reset":
        reset_shot(view, stage, seconds, small_font=small_font)
    else:
        recap_shot(view, stage, seconds, state.action, small_font=small_font)
    canvas.alpha_composite(stage)
    return canvas


def draw_coin_thumbnail(art):
    """The bottle mid-lift: the one moment the whole episode is about."""
    view = View("lift")
    draw_bottle(view, art, warm=1.0)
    draw_hands(view, art, 1.0)
    draw_gas(view, art, gas_points(view, travelled(2.4, 1.0)), halo=1.0)
    draw_lid(view, art, lift=34 * view.scale, tilt=-5)


def thumbnail(settings, board, renderer, output_path):
    """A composed still, not a frame grab: it has to survive a small feed tile."""
    stage = renderer.render_background(board, progress=0.0).convert("RGBA")
    art = Image.new("RGBA", stage.size)
    # The band is held at full pluck displacement, so it reads as a bent line.
    draw_coin_thumbnail(art)
    library = MascotLibrary(rig_root(settings.project_root))
    bear = library.frame("aha", 1.4, 800)
    art.alpha_composite(bear, (110, stage.height - 30 - bear.height))
    draw = ImageDraw.Draw(art)
    font = school_font(126)
    words = board.scenes[0].on_screen_words[0]
    width = draw.textlength(words, font=font)
    draw.text(
        ((stage.width - width) / 2, 74), words, font=font, fill=INK, stroke_width=2, stroke_fill=INK
    )
    draw.line(
        [((stage.width - width) / 2, 214), ((stage.width + width) / 2, 214)],
        fill=CORAL,
        width=9,
    )
    stage.alpha_composite(art)
    stage.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS).save(
        output_path, format="JPEG", quality=94, optimize=True
    )
