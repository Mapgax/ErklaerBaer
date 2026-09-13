"""Reusable falling-objects template: a drop rig, measured beats and one fall law.

All coordinates are in a stable 1920x1080 stage. The rig lives in a world measured in
pixels above its own floor, and every shot maps that world through a view anchored on a
floor line. In a shot with the bear, that line is where the bear's own feet stand, read from
the baked library, so the rig and the bear share a ground instead of two typed numbers.

Everything that falls obeys one of three curves, each derived here once. The episode's sound
anchors import the same timing constants, so a landing on screen and the knock under it
cannot drift apart. The relations those constants must keep are asserted in the tests.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from .collage_guitar import CORAL, CREAM, INK, PEN, ROOT, TEAL, material
from .mascot_library import MascotLibrary, mascot_origin, rig_root
from .renderer import school_font

STAGE = (1920, 1080)
# Nothing a shot draws may reach the heading the renderer puts above this line.
HEADING_FLOOR = 262.0
TEXT_X = 214.0
TEXT_ROWS = (298.0, 376.0, 454.0)
CAPTION_Y = 560.0

# World geometry, in pixels at scale 1, measured up from the floor.
LANE_STONE = 1090.0
LANE_OTHER = 1335.0
CENTRE_X = (LANE_STONE + LANE_OTHER) / 2
POST_X = 1520.0
POST_WIDTH = 46.0
DROP = 520.0
FLAP_LEFT = 1000.0
FLAP_THICKNESS = 22.0
FLOOR_LEFT, FLOOR_RIGHT = 860.0, 1680.0
# The floor of a shot without the bear, and the flap line of the prediction close-up.
FREE_FLOOR = 930.0
PREDICT_FLAP_Y = 600.0

STONE = (164.0, 104.0)
MARBLE = 70.0
# A sheet seen slightly from above: its far edge is skewed back so it reads as paper.
SHEET = (230.0, 34.0)
SHEET_SKEW = 1.1
BALL = 86.0
BALL_POINTS = 12

# A science mark is about one percent of frame width.
AIR_RADIUS = 9.5
AIR_SPACING = 64.0
# Capped below the gap between neighbours, so pushed marks never run into each other.
AIR_PUSH = 24.0
# The field stops short of the flap where it hangs against the post.
AIR_LEFT, AIR_RIGHT = 900.0, POST_X - POST_WIDTH / 2 - FLAP_THICKNESS - 45.0
AIR_TOP, AIR_BOTTOM = DROP - 50.0, 30.0
AIR_FEATHER = 150.0

# Timing. The drawing is slowed and says so; a real one-metre drop lasts under half a second.
FALL_SECONDS = 1.6
GRAVITY = 2 * DROP / FALL_SECONDS**2
FLAP_SECONDS = 0.14
# The flap opens this long after "De klep gaat open." ends.
RELEASE_DELAY = 0.25
# The crumpled ball meets a little air: it takes this factor longer over the same drop.
BALL_LAG = 1.05
PAPER_SECONDS = 7.0
PAPER_SETTLE = 0.25
CRUMPLE_DELAY = 0.1
CRUMPLE_SECONDS = 1.0
# Authored pauses that must hold the release and the knock, or the crunch, in silence.
KNOCK_SECONDS = 0.3
RELEASE_PAUSE = 2.4
CRUMPLE_PAUSE = 1.5
STROBE_STEPS = 5

STONE_FACE = "#9a948a"
STONE_LIGHT = "#b9b3a8"
STONE_DARK = "#6c675f"
GLASS = "#7f9c98"
GLASS_FILL = "#d6e6e3"
POST = "#b08a5c"
FLAP = "#c7a577"
PAD = "#6f9a92"
SHADOW = "#58452b"

# One camera per framing: (scale, screen x of the rig centre).
VIEWS = {
    "weigh": (1.5, 1300.0),
    "establish": (0.95, 1250.0),
    "predict": (1.5, 1300.0),
    "drop": (1.0, 980.0),
    "landed": (1.7, 1260.0),
    "strobe": (1.0, 900.0),
    "air": (1.0, 1000.0),
    "crumple": (0.92, 1310.0),
    "recap": (1.0, 1330.0),
}

RECAP_ROWS = (
    ("zwaar en licht: even snel", "compare"),
    ("plat blad: de lucht remt", "resist"),
    ("prop: bijna even snel", "fall"),
)


# --- the bear, as the library measured it --------------------------------------------------


@lru_cache(maxsize=16)
def bear_box(action: str, height_fraction: float, framing: str) -> tuple[float, ...]:
    """Screen box (left, top, right, bottom) the baked bear really covers in this shot."""
    root = rig_root(ROOT)
    crop = json.loads((root / "manifest.json").read_text())["crop"]
    actions = json.loads((root / "mascot-qa.json").read_text())["actions"]
    if action not in actions:
        raise ValueError(f"Mascot QA for {root.name} has no bounds for {action!r}")
    left, top, right, bottom = actions[action]["bounds_union"]
    height = round(height_fraction * STAGE[1])
    scale = height / (crop[3] - crop[1])
    x, baseline = mascot_origin(framing, *STAGE)
    return (
        x + (left - crop[0]) * scale,
        baseline - (crop[3] - top) * scale,
        x + (right - crop[0]) * scale,
        baseline - (crop[3] - bottom) * scale,
    )


def scene_bear_box(scene) -> tuple[float, ...]:
    return bear_box(scene.mascot.action.value, scene.mascot.height_fraction, scene.shot.framing)


class View:
    """The rig as one shot sees it: a scale, where the rig's centre sits, and its floor."""

    def __init__(self, scale: float, anchor_x: float, floor_y: float):
        self.scale = scale
        self.anchor_x = anchor_x
        self.floor_y = floor_y

    def x(self, world_x: float) -> float:
        return self.anchor_x + (world_x - CENTRE_X) * self.scale

    def y(self, height: float) -> float:
        return self.floor_y - height * self.scale

    def s(self, length: float) -> float:
        return length * self.scale


def view_for(scene) -> View:
    framing = scene.shot.framing
    scale, anchor = VIEWS[framing]
    if framing == "predict":
        # A close-up on the waiting flap; the floor is below the frame.
        floor = PREDICT_FLAP_Y + DROP * scale
    elif scene.mascot.visible:
        floor = scene_bear_box(scene)[3]
    else:
        floor = FREE_FLOOR
    return View(scale, anchor, floor)


# --- one fall law ----------------------------------------------------------------------------


def stone_height(t: float) -> float:
    """Free fall from rest: the same curve for the stone and the marble."""
    return max(0.0, DROP - 0.5 * GRAVITY * max(0.0, t) ** 2)


def ball_height(t: float) -> float:
    return stone_height(t / BALL_LAG)


def paper_height(t: float) -> float:
    """A flat sheet reaches a low speed almost at once and then drifts at that speed."""
    t = max(0.0, t)
    speed = DROP / (PAPER_SECONDS - PAPER_SETTLE)
    return max(0.0, DROP - speed * (t - PAPER_SETTLE * (1 - math.exp(-t / PAPER_SETTLE))))


def paper_sway(t: float) -> tuple[float, float]:
    """Sideways drift and tilt while it falls; still once it rests."""
    if t <= 0 or paper_height(t) <= 0:
        return 0.0, 0.0
    ease = min(1.0, t / 0.6)
    return 22 * ease * math.sin(math.tau * 0.5 * t), 9 * ease * math.sin(math.tau * 0.5 * t + 0.9)


# --- props, authored at the size they are shown ---------------------------------------------


@lru_cache(maxsize=24)
def stone_art(width: int, height: int) -> Image.Image:
    """A faceted grey stone, the same kind the bear lifts."""
    art = Image.new("RGBA", (width, height))
    d = ImageDraw.Draw(art)
    w, h = width - 1, height - 1
    outline = [
        (0.06 * w, 0.62 * h),
        (0.18 * w, 0.18 * h),
        (0.52 * w, 0.02 * h),
        (0.86 * w, 0.14 * h),
        (1.0 * w, 0.58 * h),
        (0.84 * w, 0.96 * h),
        (0.32 * w, 1.0 * h),
    ]
    d.polygon(outline, fill=STONE_FACE)
    d.polygon([(0.18 * w, 0.18 * h), (0.52 * w, 0.02 * h), (0.6 * w, 0.46 * h)], fill=STONE_LIGHT)
    d.polygon([(0.6 * w, 0.46 * h), (1.0 * w, 0.58 * h), (0.84 * w, 0.96 * h)], fill=STONE_DARK)
    d.line([*outline, outline[0]], fill=STONE_DARK, width=max(2, round(width / 45)), joint="curve")
    d.line(
        [(0.18 * w, 0.18 * h), (0.6 * w, 0.46 * h), (0.32 * w, 1.0 * h)], fill=STONE_DARK, width=1
    )
    return art


@lru_cache(maxsize=24)
def marble_art(diameter: int) -> Image.Image:
    art = Image.new("RGBA", (diameter, diameter))
    d = ImageDraw.Draw(art)
    r = diameter - 1
    d.ellipse((0, 0, r, r), fill=GLASS_FILL, outline=GLASS, width=max(2, round(diameter / 16)))
    d.arc((0.2 * r, 0.25 * r, 0.8 * r, 0.9 * r), 200, 340, fill=TEAL, width=max(2, round(r / 8)))
    d.arc((0.3 * r, 0.1 * r, 0.9 * r, 0.7 * r), 20, 150, fill=CORAL, width=max(2, round(r / 11)))
    d.ellipse((0.24 * r, 0.16 * r, 0.42 * r, 0.32 * r), fill=CREAM)
    return art


def sheet_outline(width: float, height: float) -> list[tuple[float, float]]:
    """A lying sheet as twelve points in the ball's angular order, corners included.

    Matching the order means the fold into a ball never crosses an edge over itself.
    """
    w, h = width / 2, height / 2
    corners = [
        (w, 0), (w, h), (w / 2, h), (0, h), (-w / 2, h), (-w, h),
        (-w, 0), (-w, -h), (-w / 2, -h), (0, -h), (w / 2, -h), (w, -h),
    ]  # fmt: skip
    return [(x - y * SHEET_SKEW, y) for x, y in corners]


def ball_outline(diameter: float) -> list[tuple[float, float]]:
    jitter = (0.92, 1.04, 0.88, 1.0, 0.95, 1.06, 0.9, 1.02, 0.94, 1.05, 0.89, 1.0)
    return [
        (
            math.cos(math.tau * i / BALL_POINTS) * diameter / 2 * jitter[i],
            math.sin(math.tau * i / BALL_POINTS) * diameter / 2 * jitter[i],
        )
        for i in range(BALL_POINTS)
    ]


def _mix_hex(first: str, second: str, amount: float) -> tuple[int, ...]:
    one = [int(first[i : i + 2], 16) for i in (1, 3, 5)]
    two = [int(second[i : i + 2], 16) for i in (1, 3, 5)]
    return tuple(round(a + (b - a) * amount) for a, b in zip(one, two, strict=True))


@lru_cache(maxsize=64)
def paper_art(scale: float, crumpled: float, tilt: float) -> Image.Image:
    """The same paper, from flat sheet (0) to crumpled ball (1), centred in a square."""
    sheet = sheet_outline(SHEET[0] * scale, SHEET[1] * scale)
    ball = ball_outline(BALL * scale)
    fold = crumpled * crumpled * (3 - 2 * crumpled)
    points = [
        (a[0] + (b[0] - a[0]) * fold, a[1] + (b[1] - a[1]) * fold)
        for a, b in zip(sheet, ball, strict=True)
    ]
    size = round(max(SHEET[0] + SHEET[1] * SHEET_SKEW, BALL) * scale + 8)
    art = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(art)
    shifted = [(size / 2 + x, size / 2 + y) for x, y in points]
    d.polygon(shifted, fill=_mix_hex(CREAM, "#e7dcc4", fold))
    d.line([*shifted, shifted[0]], fill=PEN, width=max(2, round(3 * scale)), joint="curve")
    if fold > 0.3:
        crease = max(1, round(2 * scale))
        for i in (1, 4, 7, 10):
            a, b = shifted[i], shifted[(i + 5) % BALL_POINTS]
            mid = (size / 2 + (a[0] + b[0] - size) * 0.18, size / 2 + (a[1] + b[1] - size) * 0.18)
            d.line([a, mid], fill=PEN, width=crease)
    if tilt:
        art = art.rotate(tilt, resample=Image.Resampling.BICUBIC)
    return art


def faded(art: Image.Image, opacity: float) -> Image.Image:
    if opacity >= 1.0:
        return art
    result = art.copy()
    result.putalpha(art.getchannel("A").point(lambda a: round(a * opacity)))
    return result


def paste_centred(stage, art, cx, bottom):
    stage.alpha_composite(art, (round(cx - art.width / 2), round(bottom - art.height)))


def contact_shadow(stage, view, x, height, width, opacity=1.0):
    """A soft shadow on the floor that darkens as the object comes down to it."""
    near = max(0.0, 1.0 - height / DROP)
    if near <= 0.05:
        return
    w = view.s(width) * (0.55 + 0.45 * near)
    blur = max(2, round(view.s(5)))
    # Drawn in a patch three blur radii wider than the ellipse, not across the whole stage.
    margin = 3 * blur
    half_h = view.s(7)
    patch = Image.new("RGBA", (round(w + 2 * margin), round(2 * half_h + 2 * margin)))
    ImageDraw.Draw(patch).ellipse((margin, margin, margin + w, margin + 2 * half_h), fill=SHADOW)
    patch.putalpha(patch.getchannel("A").point(lambda a: round(a * 0.22 * near * opacity)))
    cx, cy = view.x(x), view.y(0) + view.s(4)
    stage.alpha_composite(
        patch.filter(ImageFilter.GaussianBlur(blur)),
        (round(cx - w / 2 - margin), round(cy - half_h - margin)),
    )


# --- the rig ---------------------------------------------------------------------------------


@lru_cache(maxsize=16)
def _edge_fade(width: int, depth: int, feather: float) -> Image.Image:
    """An alpha that rises from both ends over `feather` pixels, so a strip melts into paper."""
    row = Image.new("L", (width, 1))
    row.putdata([round(255 * min(1.0, x / feather, (width - x) / feather)) for x in range(width)])
    return row.resize((width, depth), Image.Resampling.NEAREST)


def draw_floor(stage, view):
    """A kraft strip that fades into the paper at both ends instead of stopping square."""
    left, right = view.x(FLOOR_LEFT), view.x(FLOOR_RIGHT)
    top = view.y(0)
    depth = max(8, round(view.s(22)))
    width = max(1, round(right - left))
    feather = view.s(120)
    strip = material("kraft", width, depth).copy()
    strip.putalpha(_edge_fade(width, depth, feather))
    stage.alpha_composite(strip, (round(left), round(top)))
    ImageDraw.Draw(stage).line(
        [(left + feather * 0.6, top), (right - feather * 0.6, top)],
        fill=POST,
        width=max(2, round(view.s(3))),
    )


def draw_post(stage, view):
    top = view.y(DROP + 60)
    left = view.x(POST_X - POST_WIDTH / 2)
    width = max(2, round(view.s(POST_WIDTH)))
    height = max(2, round(view.y(0) - top))
    stage.alpha_composite(material("kraft", width, height), (round(left), round(top)))
    d = ImageDraw.Draw(stage)
    d.rectangle(
        (left, top, left + width, top + height), outline=POST, width=max(2, round(view.s(3)))
    )
    foot = view.s(46)
    d.rectangle(
        (view.x(POST_X) - foot, view.y(0) - view.s(12), view.x(POST_X) + foot, view.y(0)), fill=POST
    )


def draw_flap(stage, view, t):
    """The flap is the first thing that moves: it swings down on its hinge."""
    hx, hy = view.x(POST_X - POST_WIDTH / 2), view.y(DROP)
    angle = math.radians(90 * min(1.0, max(0.0, t / FLAP_SECONDS)) ** 2)
    length = view.s(POST_X - POST_WIDTH / 2 - FLAP_LEFT)
    thick = view.s(FLAP_THICKNESS)
    cos, sin = math.cos(angle), math.sin(angle)
    # px runs left from the hinge; rotating clockwise swings the free end down.
    points = [
        (hx + px * cos - py * sin, hy - px * sin + py * cos)
        for px, py in ((0, 0), (-length, 0), (-length, thick), (0, thick))
    ]
    d = ImageDraw.Draw(stage)
    d.polygon(points, fill=FLAP)
    d.line([*points, points[0]], fill=POST, width=max(2, round(view.s(3))), joint="curve")
    r = view.s(9)
    d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=INK)


def draw_rig(stage, view, t):
    draw_floor(stage, view)
    draw_post(stage, view)
    draw_flap(stage, view, t)


# --- falling things --------------------------------------------------------------------------


def draw_stone(stage, view, x, height, opacity=1.0):
    contact_shadow(stage, view, x, height, STONE[0], opacity)
    art = stone_art(round(view.s(STONE[0])), round(view.s(STONE[1])))
    paste_centred(stage, faded(art, opacity), view.x(x), view.y(height))


def draw_marble(stage, view, x, height, opacity=1.0):
    contact_shadow(stage, view, x, height, MARBLE, opacity)
    art = marble_art(round(view.s(MARBLE)))
    paste_centred(stage, faded(art, opacity), view.x(x), view.y(height))


def draw_paper(stage, view, x, height, *, crumpled=0.0, sway=(0.0, 0.0)):
    visible = SHEET[1] + (BALL - SHEET[1]) * crumpled
    contact_shadow(stage, view, x + sway[0], height, SHEET[0] + (BALL - SHEET[0]) * crumpled)
    art = paper_art(round(view.scale, 3), round(crumpled, 2), round(sway[1], 1))
    # The art is square with the paper in its middle: sit the paper, not the canvas.
    cx, bottom = view.x(x + sway[0]), view.y(height)
    stage.alpha_composite(
        art, (round(cx - art.width / 2), round(bottom - art.height / 2 - view.s(visible) / 2))
    )


def label(draw, text, xy, font, fill=INK):
    draw.text(xy, text, font=font, fill=fill, stroke_width=1, stroke_fill=fill)


def dashed(draw, start, end, fill=PEN, width=3, dash=16):
    steps = max(1, int(math.dist(start, end) // dash))
    for i in range(0, steps, 2):
        a, b = i / steps, min(1.0, (i + 1) / steps)
        draw.line(
            [
                (start[0] + (end[0] - start[0]) * a, start[1] + (end[1] - start[1]) * a),
                (start[0] + (end[0] - start[0]) * b, start[1] + (end[1] - start[1]) * b),
            ],
            fill=fill,
            width=width,
        )


# --- air -------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def air_lattice() -> tuple[tuple[float, float], ...]:
    points = []
    row = 0
    h = AIR_BOTTOM
    while h <= AIR_TOP:
        x = AIR_LEFT + (AIR_SPACING / 2 if row % 2 else 0.0)
        while x <= AIR_RIGHT:
            points.append((x, h))
            x += AIR_SPACING
        h += AIR_SPACING * 0.87
        row += 1
    return tuple(points)


def air_push(point, obstacles) -> float:
    """Air moves aside only near where a falling thing is now: never ahead, never behind."""
    x, h = point
    dx = 0.0
    for ox, oh, half_width in obstacles:
        reach = half_width + 90.0
        across = abs(x - ox)
        if across >= reach:
            continue
        near = math.exp(-(((h - oh) / 55.0) ** 2))
        dx += AIR_PUSH * near * math.tanh((x - ox) / 22.0) * (1 - across / reach)
    return dx


def draw_air(stage, view, obstacles, *, strength=1.0):
    layer = Image.new("RGBA", stage.size)
    d = ImageDraw.Draw(layer)
    r = view.s(AIR_RADIUS)
    for x, h in air_lattice():
        edge = min(x - AIR_LEFT, AIR_RIGHT - x, h - AIR_BOTTOM, AIR_TOP - h) + AIR_SPACING / 2
        alpha = max(0.0, min(1.0, edge / AIR_FEATHER))
        if alpha <= 0.02:
            continue
        sx, sy = view.x(x + air_push((x, h), obstacles)), view.y(h)
        d.ellipse(
            (sx - r, sy - r, sx + r, sy + r), fill=(52, 135, 127, round(130 * alpha * strength))
        )
    stage.alpha_composite(layer)


# --- timing from measured speech -------------------------------------------------------------


def _beat_timing(scene, segments, action) -> dict:
    beat = next((b for b in scene.mechanism.beats if b.action == action), None)
    if beat is None:
        raise ValueError(f"{scene.scene_id} ({scene.shot.framing}) needs a {action!r} beat")
    timing = next((t for t in segments if t["segment_id"] == beat.segment_id), None)
    if timing is None:
        raise ValueError(f"No measured timing for {beat.segment_id}")
    return timing


def beat_start(scene, segments, action) -> float:
    return _beat_timing(scene, segments, action)["scene_start"]


def beat_end(scene, segments, action) -> float:
    """Scene seconds at which the segment carrying this beat stops speaking."""
    timing = _beat_timing(scene, segments, action)
    return timing["scene_start"] + timing["end"] - timing["start"]


def release_time(scene, segments) -> float:
    return beat_end(scene, segments, "release") + RELEASE_DELAY


# --- shots -----------------------------------------------------------------------------------


def weigh_shot(stage, view, scene, seconds, action, *, font):
    """The bear holds the heavy stone; the light marble waits on its own felt pad."""
    d = ImageDraw.Draw(stage)
    draw_floor(stage, view)
    pad = view.s(70)
    d.ellipse(
        (
            view.x(LANE_OTHER) - pad,
            view.y(0) - view.s(16),
            view.x(LANE_OTHER) + pad,
            view.y(0) + view.s(8),
        ),
        fill=PAD,
    )
    draw_marble(stage, view, LANE_OTHER, 12)
    if action in {"weigh", "observe"} and seconds > 0.4:
        # Beside the stone the bear holds out, measured from the bear's own box.
        _, top, right, bottom = scene_bear_box(scene)
        label(d, "zwaar", (right + 90, top + 0.28 * (bottom - top)), font, fill=CORAL)
    if action == "observe" or seconds > 2.2:
        label(d, "licht", (view.x(LANE_OTHER) - 36, view.y(MARBLE + 12) - 70), font, fill=TEAL)


def establish_shot(stage, view, seconds, action, *, font):
    draw_rig(stage, view, -1.0)
    draw_stone(stage, view, LANE_STONE, DROP)
    draw_marble(stage, view, LANE_OTHER, DROP)
    d = ImageDraw.Draw(stage)
    label(d, "klep", (view.x(FLAP_LEFT) - 10, view.y(DROP) + view.s(40)), font, fill=PEN)
    if action in {"compare", "hold"}:
        grow = min(1.0, seconds / 0.8) if action == "compare" else 1.0
        y = view.y(DROP)
        left, right = view.x(LANE_STONE - 90), view.x(POST_X + 40)
        end = (left + (right - left) * grow, y)
        dashed(d, (left, y), end, fill=CORAL, width=max(2, round(view.s(4))))
        if grow >= 1.0:
            label(d, "even hoog", (right + 16, y - 24), font, fill=CORAL)


def predict_shot(stage, view):
    """Everything waits. The only marks are the two paths the child is asked about."""
    draw_rig(stage, view, -1.0)
    d = ImageDraw.Draw(stage)
    for x in (LANE_STONE, LANE_OTHER):
        dashed(d, (view.x(x), view.y(DROP - 20)), (view.x(x), view.y(20)), width=2, dash=12)
    draw_stone(stage, view, LANE_STONE, DROP)
    draw_marble(stage, view, LANE_OTHER, DROP)


def drop_shot(stage, view, scene, seconds, segments, *, font):
    t = seconds - release_time(scene, segments)
    draw_rig(stage, view, t)
    draw_stone(stage, view, LANE_STONE, stone_height(t))
    draw_marble(stage, view, LANE_OTHER, stone_height(t))
    d = ImageDraw.Draw(stage)
    label(d, "vertraagd", (TEXT_X, TEXT_ROWS[0]), font, fill=PEN)
    if t >= FALL_SECONDS:
        y = view.y(0) + view.s(28)
        dashed(d, (view.x(LANE_STONE), y), (view.x(LANE_OTHER), y), fill=CORAL, width=3)
        label(d, "tegelijk", (view.x(CENTRE_X) - 52, y + 12), font, fill=CORAL)


def landed_shot(stage, view, seconds, *, font):
    """Close on the floor: both at rest, side by side, the open flap hanging above."""
    draw_rig(stage, view, 10.0)
    draw_stone(stage, view, LANE_STONE, 0.0)
    draw_marble(stage, view, LANE_OTHER, 0.0)
    if seconds > 0.6:
        xy = (view.x(CENTRE_X) - 110, view.y(STONE[1]) - 110)
        label(ImageDraw.Draw(stage), "allebei tegelijk", xy, font, fill=CORAL)
    fade_above_heading(stage)


def strobe_shot(stage, view, scene, seconds, segments, action, *, font):
    """Where both are after equal short moments: the gaps grow, the heights stay equal."""
    draw_floor(stage, view)
    draw_post(stage, view)
    draw_flap(stage, view, 10.0)
    fall_start = beat_start(scene, segments, "fall")
    shown = max(0, min(STROBE_STEPS + 1, int((seconds - fall_start - 0.6) / 0.45) + 1))
    heights = [stone_height(k * FALL_SECONDS / STROBE_STEPS) for k in range(STROBE_STEPS + 1)]
    for k in range(shown):
        opacity = 1.0 if k == shown - 1 else 0.5
        draw_stone(stage, view, LANE_STONE, heights[k], opacity)
        draw_marble(stage, view, LANE_OTHER, heights[k], opacity)
    d = ImageDraw.Draw(stage)
    label(d, "vertraagd", (TEXT_X, TEXT_ROWS[0]), font, fill=PEN)
    if action in {"pull", "compare"}:
        top, bottom = view.y(DROP + 40), view.y(DROP - 150)
        cx = view.x(CENTRE_X)
        d.line([(cx, top), (cx, bottom)], fill=INK, width=max(3, round(view.s(6))))
        head = view.s(18)
        d.polygon(
            [(cx - head, bottom - head), (cx + head, bottom - head), (cx, bottom + head * 0.4)],
            fill=INK,
        )
        label(d, "de aarde trekt", (TEXT_X, TEXT_ROWS[1]), font)
        if seconds - beat_start(scene, segments, "pull") > 2.0:
            x = view.x(POST_X + 70)
            for k in range(1, STROBE_STEPS + 1):
                a, b = view.y(heights[k - 1]), view.y(heights[k])
                d.line([(x, a + 4), (x, b - 4)], fill=CORAL, width=max(3, round(view.s(5))))
                d.line([(x - 10, b - 4), (x + 10, b - 4)], fill=CORAL, width=3)
            label(d, "steeds sneller", (TEXT_X, TEXT_ROWS[2]), font, fill=CORAL)
    if action == "compare":
        lines = min(STROBE_STEPS + 1, int((seconds - beat_start(scene, segments, "compare")) / 0.3))
        for k in range(lines):
            y = view.y(heights[k] + MARBLE / 2)
            start, end = (view.x(LANE_STONE + 60), y), (view.x(LANE_OTHER - 26), y)
            dashed(d, start, end, fill=TEAL, width=3, dash=10)
        if lines > STROBE_STEPS:
            label(d, "steeds even hoog", (TEXT_X, CAPTION_Y), font, fill=TEAL)


def air_shot(stage, view, scene, seconds, segments, action, *, font):
    t = seconds - release_time(scene, segments)
    draw_floor(stage, view)
    draw_post(stage, view)
    stone_h, paper_h, sway = stone_height(t), paper_height(t), paper_sway(t)
    moving = []
    if t > 0 and stone_h > 0:
        moving.append((LANE_STONE, stone_h + STONE[1] / 2, STONE[0] / 2))
    if t > 0 and paper_h > 0:
        moving.append((LANE_OTHER + sway[0], paper_h, SHEET[0] / 2))
    draw_air(stage, view, moving, strength=min(1.0, seconds / 0.8))
    draw_flap(stage, view, t)
    draw_stone(stage, view, LANE_STONE, stone_h)
    draw_paper(stage, view, LANE_OTHER, paper_h, sway=sway)
    d = ImageDraw.Draw(stage)
    label(d, "vertraagd", (TEXT_X, TEXT_ROWS[0]), font, fill=PEN)
    if seconds > 1.2:
        label(d, "lucht", (TEXT_X, TEXT_ROWS[1]), font, fill=TEAL)
    if action == "resist":
        label(d, "de lucht remt het blad", (TEXT_X, TEXT_ROWS[2]), font, fill=CORAL)


def crumple_shot(stage, view, scene, seconds, segments, *, font):
    fold_start = beat_end(scene, segments, "crumple") + CRUMPLE_DELAY
    crumpled = min(1.0, max(0.0, (seconds - fold_start) / CRUMPLE_SECONDS))
    t = seconds - release_time(scene, segments)
    draw_rig(stage, view, t)
    draw_stone(stage, view, LANE_STONE, stone_height(t))
    draw_paper(stage, view, LANE_OTHER, ball_height(t), crumpled=crumpled)
    d = ImageDraw.Draw(stage)
    # Below the floor: above the rig the flap and stone would collide with the words.
    below = view.y(0) + view.s(40)
    label(d, "vertraagd", (view.x(FLOOR_LEFT), below), font, fill=PEN)
    if crumpled >= 1.0:
        label(d, "zelfde papier", (view.x(POST_X) - 180, below), font, fill=TEAL)


def recap_shot(stage, action, *, font):
    """One row per sentence, each arriving with the sentence that says it."""
    order = [row[1] for row in RECAP_ROWS]
    if action == "hold":
        shown = len(RECAP_ROWS)
    else:
        shown = order.index(action) + 1 if action in order else 0
    icon = View(0.8, 0.0, 0.0)
    d = ImageDraw.Draw(stage)
    for index, (text, _) in enumerate(RECAP_ROWS[:shown]):
        x, y = 860.0, 400.0 + index * 150.0
        if index == 0:
            stone = stone_art(round(icon.s(STONE[0])), round(icon.s(STONE[1])))
            paste_centred(stage, stone, x, y + 20)
            paste_centred(stage, marble_art(round(icon.s(MARBLE))), x + 125, y + 20)
        else:
            art = paper_art(0.8, 0.0, -9.0) if index == 1 else paper_art(0.8, 1.0, 0.0)
            stage.alpha_composite(art, (round(x + 40 - art.width / 2), round(y - art.height / 2)))
        colour = CORAL if index == shown - 1 and action != "hold" else INK
        label(d, f"{index + 1}. {text}", (1070.0, y - 30), font, fill=colour)


def fade_above_heading(stage, top=HEADING_FLOOR, span=70.0):
    """A close-up's tall parts dissolve into the paper before they reach the heading."""
    mask = Image.new("L", stage.size, 255)
    d = ImageDraw.Draw(mask)
    d.rectangle((0, 0, stage.width, top), fill=0)
    for i in range(round(span)):
        d.line([(0, top + i), (stage.width, top + i)], fill=round(255 * i / span))
    stage.putalpha(Image.composite(stage.getchannel("A"), Image.new("L", stage.size, 0), mask))


def draw(canvas, scene, seconds, state, *, font, small_font, segments=()):
    """Render one known semantic shot. No evaluated paths or generated code.

    Labels here are read at phone width, so every one uses `font`; `small_font` belongs to
    the shared template signature and is not used by this template.
    """
    stage = Image.new("RGBA", STAGE)
    view = view_for(scene)
    framing = scene.shot.framing
    segments = list(segments)
    if framing == "weigh":
        weigh_shot(stage, view, scene, state.elapsed, state.action, font=font)
    elif framing == "establish":
        establish_shot(stage, view, state.elapsed, state.action, font=font)
    elif framing == "predict":
        predict_shot(stage, view)
    elif framing == "drop":
        drop_shot(stage, view, scene, seconds, segments, font=font)
    elif framing == "landed":
        landed_shot(stage, view, seconds, font=font)
    elif framing == "strobe":
        strobe_shot(stage, view, scene, seconds, segments, state.action, font=font)
    elif framing == "air":
        air_shot(stage, view, scene, seconds, segments, state.action, font=font)
    elif framing == "crumple":
        crumple_shot(stage, view, scene, seconds, segments, font=font)
    else:
        recap_shot(stage, state.action, font=font)
    canvas.alpha_composite(stage)
    return canvas


def thumbnail(settings, board, renderer, output_path):
    """Both mid-fall at the same height: the one picture the episode is about."""
    stage = renderer.render_background(board, progress=0.0).convert("RGBA")
    art = Image.new("RGBA", stage.size)
    view = View(1.25, 1300.0, 1010.0)
    draw_floor(art, view)
    height = stone_height(FALL_SECONDS * 0.62)
    draw_stone(art, view, LANE_STONE, height)
    draw_marble(art, view, LANE_OTHER, height)
    d = ImageDraw.Draw(art)
    y = view.y(height) - 20
    for x in range(round(view.x(LANE_STONE) + 110), round(view.x(LANE_OTHER) - 50), 26):
        d.line([(x, y), (x + 13, y)], fill=CORAL, width=6)
    library = MascotLibrary(rig_root(settings.project_root))
    bear = library.frame("surprise", 1.2, 760)
    art.alpha_composite(bear, (90, stage.height - 40 - bear.height))
    font = school_font(126)
    words = board.youtube.thumbnail_text
    width = d.textlength(words, font=font)
    d.text(
        ((stage.width - width) / 2, 60), words, font=font, fill=INK, stroke_width=2, stroke_fill=INK
    )
    stage.alpha_composite(art)
    stage.convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS).save(
        output_path, format="JPEG", quality=94, optimize=True
    )
