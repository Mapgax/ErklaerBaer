"""Cut the BFL hand out of its flat background. No generative call, no new dependency.

The prompt asked for one uniform background colour, so the cutout is keyed by flooding in
from the corners rather than tracing a silhouette by hand. Flooding respects connectivity,
so light areas inside the hand are never punched out.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TOLERANCE = 48


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "assets/library/hands/v3"
    source = Image.open(root / "hand-source.png").convert("RGB")
    width, height = source.size

    # Flood the background from every corner; a marker colour no photograph will contain.
    marker = (255, 0, 255)
    flooded = source.copy()
    for corner in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        ImageDraw.floodfill(flooded, corner, marker, thresh=TOLERANCE)
    pixels = np.asarray(flooded)
    background = np.all(pixels == np.array(marker, dtype=pixels.dtype), axis=-1)
    alpha = Image.fromarray(np.where(background, 0, 255).astype(np.uint8), "L")
    # Paper fibre leaves speckles the flood cannot cross. Opening removes anything smaller
    # than the structuring element, and the hand is far larger than any speckle.
    alpha = alpha.filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(7))
    # Keep only what is connected to the middle of the canvas, which is inside the palm.
    picker = Image.merge("RGB", (alpha, alpha, alpha))
    ImageDraw.floodfill(picker, (width // 2, height // 2), marker, thresh=10)
    chosen = np.all(np.asarray(picker) == np.array(marker, dtype=np.uint8), axis=-1)
    alpha = Image.fromarray(np.where(chosen, 255, 0).astype(np.uint8), "L")
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))
    alpha.save(root / "hand-mask.png")

    art = source.convert("RGBA")
    art.putalpha(alpha)
    box = art.getbbox()
    art = art.crop(box)
    # Fingers point up in the source; the jar is to the side, so the hand turns to face it.
    art = art.rotate(-90, resample=Image.Resampling.BICUBIC, expand=True)
    art.save(root / "hand.png")
    covered = int((np.asarray(alpha) > 128).sum())
    print(root / "hand.png", art.size, f"opaque {covered / (width * height):.1%} of the source")


if __name__ == "__main__":
    main()
