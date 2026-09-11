"""Deterministic gas motion inside an arbitrary container outline.

The previous version folded straight-line travel inside a rectangle. That is exact for a
rectangle and wrong for any real bottle: particles appeared in the sloped shoulders and the
chamfered base, outside the drawn glass.

Here a particle's *path* is precomputed once as a polyline that reflects off the actual
outline, and its position is looked up by distance travelled. Separating the path from the
speed means warming changes only how far along the path a particle has gone, so a frame is
still reproducible on its own and a particle can never leave the glass.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

# Enough path for the longest episode at the fastest speed, with room to spare.
PATH_LENGTH = 40000.0
MAX_BOUNCES = 4000


def _inside(polygon, x, y):
    """Even-odd test. The outline is a simple closed polygon, so this is exact."""
    inside = False
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        if (y1 > y) != (y2 > y):
            crossing = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < crossing:
                inside = not inside
    return inside


def _first_hit(polygon, origin, direction):
    """Distance to the outline along `direction`, and the edge normal there."""
    ox, oy = origin
    dx, dy = direction
    best = None
    for index in range(len(polygon)):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % len(polygon)]
        ex, ey = x2 - x1, y2 - y1
        denominator = dx * ey - dy * ex
        if abs(denominator) < 1e-12:
            continue
        t = ((x1 - ox) * ey - (y1 - oy) * ex) / denominator
        u = ((x1 - ox) * dy - (y1 - oy) * dx) / denominator
        if t > 1e-6 and -1e-9 <= u <= 1 + 1e-9 and (best is None or t < best[0]):
            length = math.hypot(ex, ey) or 1.0
            best = (t, (ey / length, -ex / length))
    return best


@lru_cache(maxsize=16)
def rates(count, seed):
    """A spread of speeds, because a gas has a distribution and not one shared speed."""
    generator = np.random.default_rng(seed + 91)
    return tuple((0.65 + 0.7 * generator.random(count)).tolist())


@lru_cache(maxsize=16)
def paths(polygon, count, seed, margin):
    """One reflecting polyline per particle, as (points, cumulative lengths).

    `margin` keeps a particle's centre far enough from the glass that its whole mark stays
    inside, so nothing is ever drawn straddling the wall.
    """
    shrunk = _shrink(polygon, margin)
    generator = np.random.default_rng(seed)
    angles = generator.uniform(0, 2 * math.pi, count)
    starts = _seed_points(shrunk, count, generator)
    result = []
    for (x, y), angle in zip(starts, angles.tolist(), strict=True):
        points = [(x, y)]
        lengths = [0.0]
        direction = (math.cos(angle), math.sin(angle))
        travelled = 0.0
        for _ in range(MAX_BOUNCES):
            hit = _first_hit(shrunk, points[-1], direction)
            if hit is None:
                break
            distance, normal = hit
            step = min(distance - 1e-4, PATH_LENGTH - travelled)
            if step <= 0:
                break
            px, py = points[-1]
            points.append((px + direction[0] * step, py + direction[1] * step))
            travelled += step
            lengths.append(travelled)
            if travelled >= PATH_LENGTH:
                break
            dot = direction[0] * normal[0] + direction[1] * normal[1]
            direction = (
                direction[0] - 2 * dot * normal[0],
                direction[1] - 2 * dot * normal[1],
            )
        result.append((tuple(points), tuple(lengths)))
    return tuple(result)


def _shrink(polygon, margin):
    """Move every vertex toward the centroid by `margin`. Good enough for convex outlines."""
    if margin <= 0:
        return polygon
    cx = sum(p[0] for p in polygon) / len(polygon)
    cy = sum(p[1] for p in polygon) / len(polygon)
    shrunk = []
    for x, y in polygon:
        dx, dy = x - cx, y - cy
        length = math.hypot(dx, dy) or 1.0
        scale = max(0.0, (length - margin) / length)
        shrunk.append((cx + dx * scale, cy + dy * scale))
    return tuple(shrunk)


def _seed_points(polygon, count, generator):
    """Start positions spread through the container, all of them inside it."""
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    points = []
    while len(points) < count:
        x = generator.uniform(min(xs), max(xs))
        y = generator.uniform(min(ys), max(ys))
        if _inside(polygon, x, y):
            points.append((x, y))
    return points


def positions(polygon, distance, *, count, seed, margin):
    """Every particle after travelling `distance` along its own path, at its own speed."""
    result = []
    for (points, lengths), rate in zip(
        paths(polygon, count, seed, margin), rates(count, seed), strict=True
    ):
        result.append(_at(points, lengths, min(distance * rate, lengths[-1])))
    return result


def speeds(count, seed):
    """The per-particle speed multiplier, for cues that scale with how fast a particle moves."""
    return rates(count, seed)


def _at(points, lengths, distance):
    index = int(np.searchsorted(lengths, distance, side="right")) - 1
    index = max(0, min(index, len(points) - 2))
    span = lengths[index + 1] - lengths[index]
    share = 0.0 if span <= 0 else (distance - lengths[index]) / span
    (x1, y1), (x2, y2) = points[index], points[index + 1]
    return (x1 + (x2 - x1) * share, y1 + (y2 - y1) * share)
