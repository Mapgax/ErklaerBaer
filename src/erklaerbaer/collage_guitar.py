"""Reusable paper guitar template: authored geometry, local air motion, measured beats.

All coordinates are in a stable 1920x1080 stage. Raster materials are immutable
inputs; geometry stays editable. Science animation is deterministic and never
inferred from a generated picture.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from .mascot_library import MascotLibrary, rig_root
from .renderer import school_font

INK = "#344744"
TEAL = "#34877f"
CORAL = "#c9694d"
PEN = "#8d9c96"
CREAM = "#fffcf3"
ROOT = Path(__file__).resolve().parents[2]

# One shared slowed-down frequency for string, sound box and air. The shots that
# show it are labelled, because it is far below the real pitch of the rubber band.
SHOWN_HZ = 1.4
# Air is a field, not a corridor. Marks are sized for a phone, and the
# displacement-to-spacing ratio is held at the measured 0.385 so the claim about how far
# air moves is unchanged by the larger marks.
AIR = {
    "spacing": 52.0,
    "amplitude": 20.0,
    "speed": 308.0,
    "radius": 9,
}
# The sound box, the ear and the field between and around them, in the 1920x1080 stage.
AIR_BOX = (100, 300, 880, 559)
AIR_EAR = (1462, 392, 400, 421)
AIR_BOUNDS = (892.0, 274.0, 1904.0, 1006.0)
# The field dissolves into the paper instead of ending on a straight edge.
AIR_FEATHER = 120.0
# The disturbance leaves the middle of the box face and never comes back to it.
AIR_SOURCE = (870.0, 680.4)
AIR_TRACKED = (1264.0, 680.4)
# Scene 3 closes on the moving surfaces; the air itself waits for its own scene.
SURFACE_BOX = (350, 262, 1220, 775)
# The field appears at rest and is named before the box starts pushing it.
AIR_REST_SECONDS = 1.6


@lru_cache(maxsize=16)
def material(name, width, height):
    with Image.open(ROOT / "assets/library/materials/v3/material-sheet.png") as source:
        rect = {
            "kraft": (12, 12, 500, 500),
            "edge": (524, 12, 1012, 500),
            "peach": (12, 524, 500, 1012),
            "felt": (524, 524, 1012, 1012),
        }[name]
        tile = source.crop(rect).convert("RGB")
    tile = ImageEnhance.Contrast(tile).enhance(0.45)
    return tile.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")


def layer(size, polygon, texture="kraft", brightness=1.0, outline="#947248", width=3):
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    art = ImageEnhance.Brightness(material(texture, *size)).enhance(brightness)
    art.putalpha(mask)
    if outline:
        ImageDraw.Draw(art).line([*polygon, polygon[0]], fill=outline, width=width, joint="curve")
    return art


@lru_cache(maxsize=8)
def guitar_layers(scale=1.0):
    """Author every edge at the size it will be shown, so no drawn mark is enlarged later."""

    def pts(polygon):
        return [(x * scale, y * scale) for x, y in polygon]

    def rect(values):
        return tuple(value * scale for value in values)

    def pen(value):
        return max(1, round(value * scale))

    size = (round(960 * scale), round(610 * scale))
    side = layer(
        size, pts([(100, 180), (230, 330), (230, 500), (100, 350)]), "edge", 0.94, width=pen(3)
    )
    front = layer(
        size, pts([(230, 330), (840, 330), (840, 500), (230, 500)]), "kraft", 0.89, width=pen(3)
    )
    side.alpha_composite(front)
    top = layer(
        size, pts([(100, 180), (710, 180), (840, 330), (230, 330)]), "kraft", 1.13, width=pen(3)
    )
    d = ImageDraw.Draw(top)
    d.ellipse(rect((371, 211, 589, 304)), fill="#715135", outline="#d5af70", width=pen(7))
    d.ellipse(rect((380, 219, 580, 300)), fill="#392c25")
    d.arc(rect((380, 217, 581, 305)), 180, 350, fill="#aa8054", width=pen(5))
    # Fine corrugation only along the front seam, with edge highlights.
    d.line(pts([(233, 332), (838, 332)]), fill="#e3c18a", width=pen(4))
    bridges = Image.new("RGBA", size)
    for offset in (0, 420):
        poly = [(225 + offset, 222), (243 + offset, 222), (294 + offset, 286), (276 + offset, 286)]
        block = layer(
            size,
            pts(
                [
                    (276 + offset, 286),
                    (294 + offset, 286),
                    (294 + offset, 309),
                    (276 + offset, 309),
                ]
            ),
            "edge",
            0.9,
            width=pen(3),
        )
        block.alpha_composite(layer(size, pts(poly), "kraft", 1.27, width=pen(3)))
        block.alpha_composite(
            layer(
                size,
                pts(
                    [
                        (225 + offset, 222),
                        (276 + offset, 286),
                        (276 + offset, 309),
                        (225 + offset, 245),
                    ]
                ),
                "edge",
                0.92,
                width=pen(3),
            )
        )
        bridges.alpha_composite(block)
    return side, top, bridges


def string_points(seconds, amplitude, pluck=False, y=253, scale=1.0, hertz=SHOWN_HZ):
    left = 248 + (y - 241) * 0.8
    right = left + 420
    points = []
    for u in np.linspace(0, 1, 101):
        if pluck and seconds < 1.0:
            delta = amplitude * min(seconds / 0.75, 1) * (1 - abs(2 * u - 1))
        else:
            elapsed = max(0.0, seconds - (1.0 if pluck else 0.0))
            delta = amplitude * math.cos(2 * math.pi * hertz * elapsed) * math.sin(math.pi * u)
        points.append(((left + (right - left) * u) * scale, (y + delta) * scale))
    return points


def guitar(seconds, amplitude, *, pluck=False, coupling=False, scale=1.0, hertz=SHOWN_HZ):
    side, top, bridges = guitar_layers(scale)
    result = Image.new("RGBA", side.size)
    # The base stays fixed; the soundboard and its attached bridges move together.
    # Surface displacement is deliberately magnified and labelled in the shot.
    swing = math.sin(2 * math.pi * hertz * seconds)
    dy = round(2.5 * scale * swing) if coupling and amplitude else 0
    result.alpha_composite(side)
    result.alpha_composite(top, (0, dy))
    result.alpha_composite(bridges, (0, dy))
    d = ImageDraw.Draw(result)
    pen = max(1, round(3 * scale))
    for yy in (240, 267):
        pts = string_points(0, 0, y=yy, scale=scale, hertz=hertz)
        d.line([(x, y + dy) for x, y in pts], fill="#ba7951", width=pen)
    pts = string_points(seconds, amplitude, pluck, y=253, scale=scale, hertz=hertz)
    thick = max(1, round(5 * scale))
    d.line([(x, y + dy + 3 * scale) for x, y in pts], fill="#986044", width=thick)
    d.line([(x, y + dy) for x, y in pts], fill="#efac75", width=thick)
    if coupling:
        for x, y in (pts[0], pts[-1]):
            r = (8 + 2 * swing) * scale
            d.ellipse(
                (x - r, y + dy - r, x + r, y + dy + r),
                outline=TEAL,
                width=max(1, round(4 * scale)),
            )
    if pluck and seconds < 1:
        x, y = pts[50]
        d.ellipse(
            (x - 15 * scale, y - 18 * scale, x + 15 * scale, y + 10 * scale),
            fill="#e3b294",
            outline="#aa7459",
            width=max(1, round(2 * scale)),
        )
    return result


@lru_cache(maxsize=1)
def ear():
    with Image.open(ROOT / "assets/library/ear/v3/ear.png") as source:
        return source.convert("RGBA")


def paste_prop(canvas, prop, box, shadow=True):
    x, y, w, h = map(round, box)
    art = prop.resize((w, h), Image.Resampling.LANCZOS)
    if shadow:
        shade = Image.new("RGBA", art.size, "#58452b")
        shade.putalpha(
            art.getchannel("A").point(lambda x: round(x * 0.13)).filter(ImageFilter.GaussianBlur(8))
        )
        canvas.alpha_composite(shade, (x + 5, y + 10))
    canvas.alpha_composite(art, (x, y))


@lru_cache(maxsize=4)
def air_lattice(bounds, spacing):
    """Equilibrium points on a staggered grid. They are fixed; only the disturbance moves."""
    left, top, right, bottom = bounds
    points = []
    row = 0
    y = top
    while y <= bottom:
        x = left + (spacing / 2 if row % 2 else 0.0)
        while x <= right:
            points.append((x, y))
            x += spacing
        y += spacing * 0.92
        row += 1
    return tuple(points)


def air_onset(distance, seconds, *, speed=AIR["speed"], hertz=SHOWN_HZ):
    """How far the outgoing front has taken hold at one distance from the source."""
    cycles = (speed * seconds - distance) / (speed / hertz)
    return min(1.0, max(0.0, cycles * 2))


def air_displacement(
    point, source, seconds, *, amplitude=AIR["amplitude"], speed=AIR["speed"], hertz=SHOWN_HZ
):
    """Longitudinal displacement along the outward radius, retarded by the travel time.

    The sign of the radius is what makes the wave leave the box: a point can only move
    along the line away from the source, and only after the front has reached it.
    """
    dx, dy = point[0] - source[0], point[1] - source[1]
    distance = math.hypot(dx, dy) or 1e-6
    elapsed = seconds - distance / speed
    reach = (
        amplitude
        * air_onset(distance, seconds, speed=speed, hertz=hertz)
        * math.sin(math.tau * hertz * elapsed)
    )
    return (point[0] + reach * dx / distance, point[1] + reach * dy / distance), distance


def air_visibility(point, bounds, feather=AIR_FEATHER):
    """How solid a mark is, so the field fades out instead of ending on a straight edge.

    The left edge fades over a shorter distance than the others: that side is where the box
    stands, and air that starts a hand's width away from the face would not look pushed by it.
    """
    left, top, right, bottom = bounds
    edge = min((point[0] - left) * 2.5, right - point[0], point[1] - top, bottom - point[1])
    return min(1.0, max(0.0, edge / feather))


def wavefront_layer(
    size,
    source,
    seconds,
    bounds,
    *,
    speed=AIR["speed"],
    strength=0.4,
    hertz=SHOWN_HZ,
    feather=AIR_FEATHER,
):
    """Soft rings on every density maximum, so the travelling pulse survives a small screen.

    The ring brightness comes from the same retarded phase as the particles, so the coarse
    cue and the fine cue can never drift apart. Computed at half resolution: it is soft.
    """
    width, height = size[0] // 2, size[1] // 2
    ys, xs = np.mgrid[0:height, 0:width]
    x = xs.astype(np.float32) * 2.0
    y = ys.astype(np.float32) * 2.0
    distance = np.hypot(x - source[0], y - source[1])
    cycles = (speed * seconds - distance) / (speed / hertz)
    crowding = np.clip(np.cos(math.tau * cycles), 0.0, 1.0) ** 2
    alpha = crowding * np.clip(cycles * 2.0, 0.0, 1.0) * strength
    edge = np.minimum(
        np.minimum(x - bounds[0], bounds[2] - x), np.minimum(y - bounds[1], bounds[3] - y)
    )
    alpha *= np.clip(edge / feather, 0.0, 1.0)
    art = np.zeros((height, width, 4), np.uint8)
    art[:, :, 0], art[:, :, 1], art[:, :, 2] = 52, 135, 127
    art[:, :, 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(art, "RGBA").resize(size, Image.Resampling.BILINEAR)


def draw_air_field(
    stage,
    source,
    seconds,
    *,
    bounds=AIR_BOUNDS,
    grow=1.0,
    tracked=None,
    spacing=AIR["spacing"],
    amplitude=AIR["amplitude"],
    speed=AIR["speed"],
    hertz=SHOWN_HZ,
    feather=AIR_FEATHER,
):
    """Fill the space around the box with air and let the crowding spread outward.

    `grow` scales the marks in while the field is introduced. The whole field appears at
    once, because air is already everywhere; only the disturbance travels.
    """
    if grow <= 0:
        return
    stage.alpha_composite(
        wavefront_layer(
            stage.size,
            source,
            seconds,
            bounds,
            speed=speed,
            strength=0.36 * grow,
            hertz=hertz,
            feather=feather,
        )
    )
    d = ImageDraw.Draw(stage)
    points = air_lattice(bounds, spacing)
    marked = (
        min(points, key=lambda p: math.hypot(p[0] - tracked[0], p[1] - tracked[1]))
        if tracked
        else None
    )
    for point in points:
        visible = air_visibility(point, bounds, feather)
        radius = round((AIR["radius"] + (3 if point == marked else 0)) * grow * visible)
        if radius < 1:
            continue
        (px, py), distance = air_displacement(
            point, source, seconds, amplitude=amplitude, speed=speed, hertz=hertz
        )
        rest = max(1, round(3 * grow * visible))
        d.ellipse(
            (point[0] - rest, point[1] - rest, point[0] + rest, point[1] + rest), fill="#c3cec5"
        )
        is_marked = point == marked
        if is_marked:
            # The tracked particle returns to the same place; its track states that plainly.
            dx, dy = (point[0] - source[0]) / distance, (point[1] - source[1]) / distance
            span = (amplitude + 9) * grow * visible
            d.line(
                [
                    (point[0] - dx * span, point[1] - dy * span),
                    (point[0] + dx * span, point[1] + dy * span),
                ],
                fill="#e6b7a8",
                width=4,
            )
        d.ellipse(
            (px - radius, py - radius, px + radius, py + radius),
            fill=CORAL if is_marked else TEAL,
        )


def face_bow(
    stage,
    box,
    seconds,
    source,
    *,
    speed=AIR["speed"],
    amplitude=AIR["amplitude"],
    hertz=SHOWN_HZ,
):
    """The box face bows by the displacement of the air it touches, ends pinned to its corners.

    Drawing the coupling as a bow of the face itself is what keeps it on the box: a straight
    bar carrying the same displacement slides off the edge it is supposed to belong to.
    """
    scale = box[2] / 960
    face_x = box[0] + 840 * scale
    top, bottom = box[1] + 330 * scale, box[1] + 500 * scale
    (probe_x, _), _ = air_displacement(
        (face_x + 6, source[1]), source, seconds, amplitude=amplitude, speed=speed, hertz=hertz
    )
    shift = probe_x - (face_x + 6)
    ImageDraw.Draw(stage).line(
        [
            (
                face_x + shift * math.sin(math.pi * step / 24),
                top + (bottom - top) * step / 24,
            )
            for step in range(25)
        ],
        fill=TEAL,
        width=7,
        joint="curve",
    )


def paste_guitar(
    canvas, box, seconds, amplitude, *, pluck=False, coupling=False, crop=None, hertz=SHOWN_HZ
):
    """Author the prop at the width it will occupy, so no drawn edge is enlarged afterwards."""
    x, y, width, _ = box
    scale = width / ((crop[2] - crop[0]) if crop else 960)
    art = guitar(seconds, amplitude, pluck=pluck, coupling=coupling, scale=scale, hertz=hertz)
    if crop:
        art = art.crop(tuple(round(value * scale) for value in crop))
    paste_prop(canvas, art, (x, y, art.width, art.height))


def stroke_reveal(draw, points, fraction, *, fill=PEN, width=3):
    """Draw the leading `fraction` of a polyline by arc length; return the pen tip."""
    lengths = [0.0]
    for start, end in zip(points, points[1:], strict=False):
        lengths.append(lengths[-1] + math.hypot(end[0] - start[0], end[1] - start[1]))
    if lengths[-1] <= 0 or fraction <= 0:
        return points[0]
    target = lengths[-1] * min(1.0, fraction)
    drawn = [points[0]]
    for index in range(1, len(points)):
        if lengths[index] <= target:
            drawn.append(points[index])
            continue
        share = (target - lengths[index - 1]) / (lengths[index] - lengths[index - 1])
        start, end = points[index - 1], points[index]
        drawn.append(
            (start[0] + (end[0] - start[0]) * share, start[1] + (end[1] - start[1]) * share)
        )
        break
    if len(drawn) > 1:
        draw.line(drawn, fill=fill, width=width, joint="curve")
    return drawn[-1]


EAR_BOX = (60, 545, 470, 299)
EAR_PROP = (1010, 205, 640, 672)
EAR_BOUNDS = (482.0, 442.0, 1336.0, 986.0)
EAR_SOURCE = (471.2, 748.2)
# The cutaway is a window: nothing drawn for it may cross its rim.
CUTAWAY = {
    "cx": 1226.0,
    "cy": 587.0,
    "radius": 98.0,
    "half": 58.0,
    "wall_inset": 3.0,
    "drum_inset": 10.0,
}
MEMBRANE_PUSH = AIR["amplitude"] * 0.8


def cutaway_parts(push, *, cx, cy, radius, half, wall_inset, drum_inset, max_push=MEMBRANE_PUSH):
    """Canal walls and eardrum, sized from the rim so no stroke can ever leave the window.

    The walls run out to the rim itself, less half their own stroke, so they meet it rather
    than floating inside it or crossing it. The drum is pulled back by the largest bulge it
    will ever have, so even the widest frame of the cycle still clears the rim.
    """

    def chord(inset):
        return math.sqrt(max(0.0, (radius - inset) ** 2 - half**2))

    drum = cx + chord(drum_inset) - max_push
    left = cx - chord(wall_inset)
    return (
        [(left, cy - half), (drum, cy - half)],
        [(left, cy + half), (drum, cy + half)],
        [
            (drum + push * math.sin(math.pi * step / 40), cy - half + 2 * half * step / 40)
            for step in range(41)
        ],
        drum,
    )


def hearing_shot(stage, seconds):
    """A closer look: the arriving pressure change moves a drawn eardrum."""
    d = ImageDraw.Draw(stage)
    paste_guitar(stage, EAR_BOX, seconds, 9, coupling=True)
    draw_air_field(
        stage,
        EAR_SOURCE,
        seconds,
        bounds=EAR_BOUNDS,
        tracked=None,
        grow=min(1.0, seconds / 0.8),
    )
    face_bow(stage, EAR_BOX, seconds, EAR_SOURCE)
    paste_prop(stage, ear(), EAR_PROP)
    cx, cy, radius = CUTAWAY["cx"], CUTAWAY["cy"], CUTAWAY["radius"]
    opened = min(1.0, seconds / 1.0)
    size = round(radius * 2 + 4)
    disc = Image.new("RGBA", (size, size))
    ImageDraw.Draw(disc).ellipse((2, 2, size - 3, size - 3), fill=CREAM)
    disc.putalpha(disc.getchannel("A").point(lambda a, k=opened: round(a * k)))
    stage.alpha_composite(disc, (round(cx - radius - 2), round(cy - radius - 2)))
    stroke_reveal(
        d,
        [
            (
                cx + radius * math.cos(math.tau * step / 72),
                cy + radius * math.sin(math.tau * step / 72),
            )
            for step in range(73)
        ],
        opened,
        width=4,
    )
    settle = min(1.0, max(0.0, (seconds - 1.0) / 0.5))
    if settle <= 0:
        return
    # The membrane waits for the pressure change to travel the distance it is drawn at.
    _, _, _, drum = cutaway_parts(0.0, **CUTAWAY)
    distance = math.hypot(drum - EAR_SOURCE[0], cy - EAR_SOURCE[1])
    elapsed = seconds - distance / AIR["speed"]
    push = MEMBRANE_PUSH * air_onset(distance, seconds) * math.sin(math.tau * SHOWN_HZ * elapsed)
    top, bottom, membrane, _ = cutaway_parts(push, **CUTAWAY)
    # The canal runs the width of the cutaway and ends at the drum, as it does in an ear.
    stroke_reveal(d, top, settle, fill=INK)
    stroke_reveal(d, bottom, settle, fill=INK)
    stroke_reveal(d, membrane, settle, fill=CORAL, width=6)


# Same speed of sound, different rate: what changes is the spacing of the rings, not how
# fast they travel. Both rows start together so the fronts stay level on screen.
PITCH_ROWS = (
    ((110, 280, 470, 299), (534.0, 320.0, 1870.0, 646.0), 1.8, "Sneller: hoge toon", 596),
    ((110, 690, 470, 299), (534.0, 730.0, 1870.0, 1056.0), 0.6, "Langzamer: lage toon", 1006),
)
PITCH_FEATHER = 70.0


def pitch_shot(stage, seconds, *, small_font):
    """Two identical boxes at different rates, so pitch is a difference the eye can see."""
    d = ImageDraw.Draw(stage)
    grow = min(1.0, max(0.0, seconds / 0.9))
    for box, bounds, ratio, caption, caption_y in PITCH_ROWS:
        hertz = SHOWN_HZ * ratio
        scale = box[2] / 960
        source = (box[0] + 840 * scale, box[1] + 415 * scale)
        paste_guitar(stage, box, seconds, 9, coupling=True, hertz=hertz)
        draw_air_field(
            stage,
            source,
            seconds,
            bounds=bounds,
            grow=grow,
            tracked=None,
            hertz=hertz,
            feather=PITCH_FEATHER,
        )
        face_bow(stage, box, seconds, source, hertz=hertz)
        d.text((150, caption_y), caption, font=small_font, fill=INK)


def surface_shot(stage, seconds, *, small_font):
    """The whole box, seen wide, with the face that will do the pushing already moving."""
    paste_guitar(stage, SURFACE_BOX, seconds, 14, coupling=True)
    scale = SURFACE_BOX[2] / 960
    source = (SURFACE_BOX[0] + 840 * scale, SURFACE_BOX[1] + 415 * scale)
    face_bow(stage, SURFACE_BOX, seconds, source)
    ImageDraw.Draw(stage).text((196, 952), "Uitvergroot en vertraagd", font=small_font, fill=INK)


def air_shot(stage, seconds, action, *, small_font):
    """The box, the air around it and the ear, with the crowding spreading outward.

    The shot opens on still air that is named before anything travels through it, so the
    first thing a child sees moving is the cause and not the effect. The tracked particle
    joins on the beat that says the particles stay near their own place.
    """
    clock = max(0.0, seconds - AIR_REST_SECONDS)
    grow = min(1.0, max(0.0, (seconds - 0.15) / 1.1))
    paste_guitar(stage, AIR_BOX, clock, 12 * min(1.0, clock / 0.4), coupling=True)
    draw_air_field(
        stage,
        AIR_SOURCE,
        clock,
        grow=grow,
        tracked=AIR_TRACKED if action == "propagate" else None,
    )
    face_bow(stage, AIR_BOX, clock, AIR_SOURCE)
    paste_prop(stage, ear(), AIR_EAR)
    d = ImageDraw.Draw(stage)
    if grow > 0.35:
        d.text((196, 884), "Luchtdeeltjes", font=small_font, fill=INK)
    d.text((196, 952), "Uitvergroot en vertraagd", font=small_font, fill=INK)


def draw(canvas, scene, seconds, state, *, font, small_font, segments=()):
    """Render one known semantic shot. No evaluated paths or generated code.

    Every template receives the measured `segments`; this one times its beats from `state`.
    """
    framing = scene.shot.framing
    # Scene 3 changes composition on its second beat, so no picture is held for two scenes.
    if framing == "attachments" and state.action == "surface":
        framing, seconds = "surface", state.elapsed
    stage = Image.new("RGBA", (1920, 1080))
    d = ImageDraw.Draw(stage)
    action = state.action
    amp = 19.0 if action in {"pluck", "vibrate", "sound"} else 0.0
    if framing == "decay":
        amp = 24 * math.exp(-seconds / 3.5)
    if framing == "reaction":
        # Quiet prediction hold; separate shot gives the bear useful screen space.
        paste_guitar(stage, (850, 410, 730, 465), seconds, 7)
    elif framing == "establish":
        paste_guitar(stage, (690, 270, 1000, 635), state.elapsed, amp, pluck=action == "pluck")
    elif framing in {"string", "attachments"}:
        paste_guitar(
            stage,
            (230, 370, 1460, 450),
            state.elapsed,
            22.0,
            coupling=framing == "attachments",
            crop=(175, 155, 790, 345),
        )
        d.text((250, 875), "Vertraagd", font=small_font, fill=INK)
    elif framing == "surface":
        surface_shot(stage, seconds, small_font=small_font)
    elif framing == "air":
        air_shot(stage, seconds, action, small_font=small_font)
    elif framing == "ear":
        # The scene's second beat is about pitch, which needs a comparison, not a close-up.
        if action == "vibrate":
            pitch_shot(stage, state.elapsed, small_font=small_font)
        else:
            hearing_shot(stage, seconds)
            d.text((150, 1006), "Uitvergroot en vertraagd", font=small_font, fill=INK)
    else:
        paste_guitar(stage, (250, 285, 1100, 699), seconds, amp, coupling=amp > 0.1)
        if framing == "recap":
            paste_prop(stage, ear(), (1360, 415, 230, 242))
    canvas.alpha_composite(stage.resize(canvas.size, Image.Resampling.LANCZOS))
    return canvas


def thumbnail(settings, board, renderer, output_path):
    """A composed still, not a frame grab: it has to survive a small feed tile."""
    stage = renderer.render_background(board, progress=0.0).convert("RGBA")
    art = Image.new("RGBA", stage.size)
    # The band is held at full pluck displacement, so it reads as a bent line.
    paste_guitar(art, (770, 292, 1080, 686), 0.72, 50.0, pluck=True)
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
