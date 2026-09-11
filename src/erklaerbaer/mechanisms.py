"""Deterministic science diagrams driven by measured narration segment starts."""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import ImageDraw

from .models import Scene

INK = (42, 53, 52)
TEAL = (24, 137, 126)
BLUE = (72, 164, 207)
CORAL = (238, 102, 76)
WHITE = (255, 252, 243)
GOLD = (244, 181, 38)
BROWN = (148, 106, 71)


@dataclass(frozen=True)
class BeatState:
    action: str
    elapsed: float


def beat_at(scene: Scene, moment: float, timings: list[dict]) -> BeatState:
    if not scene.mechanism:
        raise ValueError("Explicit mechanism required")
    starts = {t["segment_id"]: t["scene_start"] for t in timings if t["scene_id"] == scene.scene_id}
    if not all(beat.segment_id in starts for beat in scene.mechanism.beats):
        raise ValueError("Measured segment timings required for each mechanism beat")
    current = scene.mechanism.beats[0]
    start = starts[current.segment_id]
    for beat in scene.mechanism.beats:
        if starts[beat.segment_id] <= moment and beat.action != current.action:
            current = beat
            start = starts[beat.segment_id]
    return BeatState(current.action, max(0, moment - start))


class ScienceStage:
    def __init__(self, draw: ImageDraw.ImageDraw, area: tuple[float, float, float, float]):
        self.draw = draw
        self.x, self.y, right, bottom = area
        self.w = right - self.x
        self.h = bottom - self.y
        self.unit = min(self.w, self.h)

    def xy(self, x, y):
        return self.x + x * self.w, self.y + y * self.h

    def line(self, points, fill=INK, width=0.006):
        self.draw.line(
            [self.xy(*p) for p in points],
            fill=fill,
            width=max(1, round(self.unit * width)),
            joint="curve",
        )

    def ellipse(self, x, y, rx, ry, fill, outline=None):
        self.draw.ellipse(
            (*self.xy(x - rx, y - ry), *self.xy(x + rx, y + ry)),
            fill=fill,
            outline=outline,
            width=max(1, round(self.unit * 0.005)),
        )

    def poly(self, points, fill, outline=None):
        self.draw.polygon([self.xy(*p) for p in points], fill=fill)
        if outline:
            self.line([*points, points[0]], outline)

    def arrow(self, start, end, color=CORAL, width=0.006):
        self.line([start, end], color, width)
        a = math.atan2((end[1] - start[1]) * self.h, (end[0] - start[0]) * self.w)
        x, y = self.xy(*end)
        length = self.unit * 0.022
        self.draw.polygon(
            [
                (x, y),
                (x - length * math.cos(a - 0.55), y - length * math.sin(a - 0.55)),
                (x - length * math.cos(a + 0.55), y - length * math.sin(a + 0.55)),
            ],
            fill=color,
        )

    def render(self, kind, state):
        {
            "gas-pressure": self.gas,
            "vibrating-string": self.string,
            "animal-observation": self.animals,
        }[kind](state)

    def gas(self, state):
        action, t = state.action, state.elapsed
        # Keep the bottle proportions stable in both wide and shared shots.
        center = self.x + self.w / 2
        self.w = min(self.w, self.h * 1.7)
        self.x = center - self.w / 2
        warm = action in {"heat", "faster", "pressure", "lift", "vent"}
        bottle = [
            (0.38, 0.23),
            (0.38, 0.34),
            (0.28, 0.43),
            (0.28, 0.88),
            (0.72, 0.88),
            (0.72, 0.43),
            (0.62, 0.34),
            (0.62, 0.23),
        ]
        self.poly(bottle, (229, 240, 232))
        self.line(bottle, TEAL, 0.013)
        self.line([(0.38, 0.23), (0.62, 0.23)], TEAL, 0.01)
        self.line([(0.30, 0.86), (0.70, 0.86)], (153, 195, 182), 0.004)
        self.line([(0.5, 0.27), (0.5, 0.35)], WHITE, 0.003)
        # The drawn glass geometry is exactly fixed across all phases.
        lift = 0
        if action == "lift":
            lift = 0.12 * min(1, t / 0.6)
        if action == "vent":
            lift = 0.12
        if action == "reset":
            lift = 0.12 * (1 - min(1, t / 0.55))
        self.ellipse(0.5, 0.217 - lift, 0.139, 0.023, GOLD, INK)
        self.line([(0.39, 0.208 - lift), (0.61, 0.208 - lift)], WHITE, 0.004)
        count = 18 if action not in {"vent", "reset"} else 12
        speed = 0.14 if action not in {"faster", "pressure", "lift", "vent"} else 0.29
        # Analytic reflecting trajectories, with broad inter-particle spacing.
        for i in range(count):
            xx = (0.173 * i + speed * t * (1 if i % 2 else -1)) % 2
            yy = (0.271 * i + speed * t * 0.79 * (1 if i % 3 else -1)) % 2
            px = 0.315 + 0.37 * (1 - abs(xx - 1))
            py = 0.47 + 0.35 * (1 - abs(yy - 1))
            if warm:
                self.line([(px - 0.012, py + 0.016), (px, py)], (172, 178, 149), 0.003)
            self.ellipse(px, py, 0.006, 0.009, BLUE)
        if warm:
            for side in [-1, 1]:
                for yy in [0.55, 0.66, 0.77]:
                    self.arrow((0.5 + side * 0.40, yy), (0.5 + side * 0.24, yy), CORAL, 0.01)
        if action in {"pressure", "lift"}:
            for xx in [0.42, 0.5, 0.58]:
                self.arrow((xx, 0.36), (xx, 0.26 - lift), TEAL, 0.008)
            for yy in [0.51, 0.65, 0.79]:
                self.arrow((0.36, yy), (0.285, yy), TEAL)
                self.arrow((0.64, yy), (0.715, yy), TEAL)
            # Ambient pressure is present on the outer face as well.
            for xx in [0.45, 0.55]:
                self.arrow((xx, 0.04), (xx, 0.16 - lift * 0.5), (136, 148, 144), 0.005)
        if action == "vent":
            for side in [-1, 1]:
                self.arrow((0.5 + side * 0.09, 0.24), (0.5 + side * 0.29, 0.13), BLUE, 0.006)
                for i in range(5):
                    p = (t * 0.65 + i * 0.2) % 1
                    self.ellipse(
                        0.5 + side * (0.11 + 0.22 * p), 0.24 - 0.12 * p, 0.006, 0.009, BLUE
                    )

    def string(self, state):
        a, t = state.action, state.elapsed
        active = a in {"pluck", "vibrate", "sound", "damp"}
        amp = 0.055 if active else 0
        if a == "pluck":
            amp *= min(1, t / 0.25)
        if a == "damp":
            amp *= math.exp(-t * 0.55)
        phase = math.sin(t * math.tau * 1.4)
        jiggle = 0.003 * phase if active else 0
        self.poly(
            [
                (0.1, 0.56 + jiggle),
                (0.51, 0.56 + jiggle),
                (0.56, 0.63 + jiggle),
                (0.15, 0.63 + jiggle),
            ],
            (214, 170, 112),
            INK,
        )
        self.poly(
            [
                (0.15, 0.63 + jiggle),
                (0.56, 0.63 + jiggle),
                (0.56, 0.87 + jiggle),
                (0.15, 0.87 + jiggle),
            ],
            (190, 145, 92),
            INK,
        )
        self.poly(
            [
                (0.1, 0.56 + jiggle),
                (0.15, 0.63 + jiggle),
                (0.15, 0.87 + jiggle),
                (0.1, 0.80 + jiggle),
            ],
            (159, 118, 79),
            INK,
        )
        self.ellipse(0.34, 0.72 + jiggle, 0.073, 0.045, (82, 67, 49))
        # Two fixed support points; string displacement vanishes at both ends.
        points = [
            (0.14 + 0.38 * i / 80, 0.46 + amp * phase * math.sin(math.pi * i / 80))
            for i in range(81)
        ]
        self.line(points, CORAL, 0.009)
        for xx in [0.14, 0.52]:
            self.line([(xx, 0.46), (xx, 0.62)], INK, 0.007)
            self.ellipse(xx, 0.46, 0.007, 0.01, TEAL)
        if a in {"pluck", "vibrate"}:
            self.arrow((0.33, 0.31), (0.33, 0.42), TEAL, 0.008)
            self.arrow((0.33, 0.52), (0.33, 0.60), TEAL, 0.006)
        # An air lattice oscillates locally. Compression travels to the right.
        if a == "sound":
            for row in range(5):
                for col in range(14):
                    rest = 0.60 + col * 0.018
                    displacement = 0.006 * math.sin(math.tau * (col / 6 - t * 1.4))
                    self.ellipse(rest + displacement, 0.50 + row * 0.044, 0.0025, 0.004, BLUE)
            self.arrow((0.61, 0.40), (0.84, 0.40), BLUE)
        self.ellipse(0.92, 0.61, 0.049, 0.14, (232, 182, 132), INK)
        self.line(
            [
                (0.929, 0.51),
                (0.90, 0.51),
                (0.90, 0.61),
                (0.934, 0.60),
                (0.935, 0.67),
                (0.915, 0.71),
            ],
            BROWN,
            0.007,
        )

    def animal(self, kind, cx, cy, scale=1):
        # Legs drawn as paired independent limbs with unobstructed joints.
        pairs = {"insect": 3, "spider": 4, "woodlouse": 7}[kind]
        bodyw = 0.030 * scale
        bodyh = (0.11 if kind == "woodlouse" else 0.065) * scale
        for i in range(pairs):
            yy = cy + ((i / (pairs - 1)) - 0.5) * bodyh * 1.45
            for side in [-1, 1]:
                self.line(
                    [
                        (cx + side * bodyw * 0.6, yy),
                        (cx + side * bodyw * 1.45, yy - 0.02 * scale),
                        (cx + side * bodyw * 2.0, yy + 0.032 * scale),
                    ],
                    INK,
                    0.006,
                )
        color = {"insect": TEAL, "spider": BROWN, "woodlouse": (104, 120, 126)}[kind]
        self.ellipse(cx, cy, bodyw, bodyh, color, INK)
        if kind == "insect":
            self.ellipse(cx, cy + 0.14 * scale, bodyw * 1.15, 0.08 * scale, TEAL, INK)
            self.ellipse(cx, cy - 0.10 * scale, 0.026 * scale, 0.047 * scale, TEAL, INK)
        elif kind == "spider":
            self.ellipse(cx, cy + 0.13 * scale, 0.043 * scale, 0.08 * scale, BROWN, INK)
        else:
            for i in range(1, 7):
                yy = cy - bodyh + i * bodyh * 2 / 7
                self.line([(cx - bodyw * 0.8, yy), (cx + bodyw * 0.8, yy)], (185, 195, 195), 0.003)
        if kind != "spider":
            heady = cy - (0.14 if kind == "insect" else 0.11) * scale
            for side in [-1, 1]:
                self.line(
                    [
                        (cx + side * 0.02 * scale, heady),
                        (cx + side * 0.045 * scale, heady - 0.05 * scale),
                    ],
                    INK,
                    0.003,
                )

    def animals(self, state):
        a, t = state.action, state.elapsed
        if a in {"insect", "spider", "woodlouse"}:
            self.animal(a, 0.5, 0.50, 1.65)
            pairs = {"insect": 3, "spider": 4, "woodlouse": 7}[a]
            for i in range(pairs):
                x = 0.5 + (i - (pairs - 1) / 2) * 0.05
                self.ellipse(x, 0.87, 0.007, 0.01, TEAL)
                self.ellipse(x, 0.92, 0.007, 0.01, TEAL)
            return
        if a == "compare":
            for x, kind in [(0.17, "insect"), (0.50, "spider"), (0.83, "woodlouse")]:
                self.animal(kind, x, 0.49, 1.05)
            return
        self.poly([(0.09, 0.84), (0.91, 0.84), (0.91, 0.95), (0.09, 0.95)], (190, 155, 108))
        for x, kind in [(0.28, "insect"), (0.5, "woodlouse"), (0.73, "spider")]:
            self.animal(kind, x, 0.71, 0.58)
        reveal = min(1, t / 1.1) if a == "reveal" else 0
        dy = -0.36 * reveal
        stone = [
            (0.13, 0.59 + dy),
            (0.26, 0.45 + dy),
            (0.65, 0.43 + dy),
            (0.83, 0.55 + dy),
            (0.89, 0.85 + dy),
            (0.13, 0.85 + dy),
        ]
        self.poly(stone, (132, 142, 139), INK)
        self.line([(0.26, 0.52 + dy), (0.52, 0.49 + dy), (0.70, 0.54 + dy)], (184, 191, 181), 0.014)
