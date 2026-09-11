"""Measure the magnifier lens across the neutral loop, for any baked frame library.

The defect the owner saw is the lens changing shape as the head turns. A bounding box is a
poor instrument for that: an ellipse can change shape a lot inside a box that barely moves.
This fits the lens glass itself and reports its two axes, so a rebind can be judged on
numbers as well as by eye.

Usage: qa_v3_lupe.py assets/mascot/rig/v3 [more rigs...]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from erklaerbaer.mascot_library import MascotLibrary
from erklaerbaer.renderer import school_font

HEIGHT = 900
SAMPLES = 16


def lens_axes(clip):
    """Fit the pale lens glass and return its major and minor axes in pixels."""
    a = np.asarray(clip.convert("RGBA")).astype(int)
    h, w = a.shape[:2]
    r, g, b, alpha = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    # Pale blue-grey glass, only in the quadrant the magnifier occupies.
    glass = (alpha > 150) & (r > 130) & (g > r + 4) & (b > r + 4) & (abs(g - b) < 30)
    window = np.zeros_like(glass)
    window[int(h * 0.08) : int(h * 0.42), int(w * 0.46) :] = True
    glass &= window
    ys, xs = np.nonzero(glass)
    if len(xs) < 400:
        return None
    points = np.stack([xs - xs.mean(), ys - ys.mean()])
    # Principal axes of the pixel cloud: four standard deviations spans the ellipse.
    eigenvalues = np.linalg.eigvalsh(np.cov(points))
    minor, major = (4 * math.sqrt(max(v, 0.0)) for v in eigenvalues)
    return major, minor, len(xs), xs.mean(), ys.mean()


def report(root: Path):
    library = MascotLibrary(root)
    rows = []
    for index in range(SAMPLES):
        seconds = index * 4.0 / SAMPLES
        measured = lens_axes(library.frame("neutral", seconds, HEIGHT))
        if measured is None:
            continue
        major, minor, area, cx, cy = measured
        rows.append((seconds, major, minor, major / minor, area))
    if not rows:
        print(f"{root}: lens not found")
        return None
    majors = [r[1] for r in rows]
    minors = [r[2] for r in rows]
    ratios = [r[3] for r in rows]
    print(f"\n== {root}")
    print(f"{'t':>5} {'major':>7} {'minor':>7} {'ratio':>6}")
    for seconds, major, minor, ratio, _ in rows:
        print(f"{seconds:5.2f} {major:7.1f} {minor:7.1f} {ratio:6.3f}")
    spread = (max(ratios) - min(ratios)) / min(ratios)
    print(f"major {min(majors):.1f}..{max(majors):.1f}  minor {min(minors):.1f}..{max(minors):.1f}")
    print(f"axis ratio {min(ratios):.3f}..{max(ratios):.3f}  spread {100 * spread:.1f}%")
    return spread


def strip(root: Path, out: Path):
    library = MascotLibrary(root)
    cell = (280, 280)
    moments = [i * 4.0 / 8 for i in range(8)]
    sheet = Image.new("RGB", (cell[0] * len(moments) + 20, cell[1] + 80), "#f6f1e4")
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (14, 16), f"{root.name}: lens across the neutral loop", font=school_font(28), fill="#344744"
    )
    for index, seconds in enumerate(moments):
        clip = library.frame("neutral", seconds, HEIGHT)
        measured = lens_axes(clip)
        if measured is None:
            continue
        _, _, _, cx, cy = measured
        half = 105
        crop = clip.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half)))
        tile = Image.new("RGB", cell, "#f6f1e4")
        tile.paste(
            crop.resize(cell, Image.Resampling.LANCZOS),
            (0, 0),
            crop.resize(cell, Image.Resampling.LANCZOS),
        )
        sheet.paste(tile, (10 + index * cell[0], 52))
        draw.text(
            (14 + index * cell[0], 26), f"{seconds:.1f}s", font=school_font(22), fill="#344744"
        )
    sheet.save(out, quality=94)
    print("wrote", out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rigs", nargs="+", type=Path)
    parser.add_argument("--strips", type=Path, default=Path("build/v3/lupe"))
    args = parser.parse_args()
    args.strips.mkdir(parents=True, exist_ok=True)
    for rig in args.rigs:
        report(rig)
        strip(rig, args.strips / f"lens-{rig.name}.jpg")


if __name__ == "__main__":
    main()
