"""Editable silhouette mask for the BFL ear; no generative call or new dependency."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CURVES = [
    [(549, 128), (690, 116), (786, 224), (778, 372)],
    [(778, 372), (785, 535), (650, 651), (596, 738)],
    [(596, 738), (553, 804), (503, 864), (421, 869)],
    [(421, 869), (340, 881), (285, 823), (275, 740)],
    [(275, 740), (262, 680), (251, 628), (265, 552)],
    [(265, 552), (232, 502), (254, 425), (271, 363)],
    [(271, 363), (279, 269), (347, 174), (437, 142)],
    [(437, 142), (482, 129), (515, 123), (549, 128)],
]


def main():
    root = Path(__file__).resolve().parents[1] / "assets/library/ear/v3"
    source = Image.open(root / "ear-source.png").convert("RGBA")
    points = []
    for curve in CURVES:
        a, b, c, d = np.asarray(curve, dtype=float)
        for t in np.linspace(0, 1, 60):
            points.append(
                tuple(
                    (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t**3 * d
                )
            )
    mask = Image.new("L", source.size)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.7))
    mask.save(root / "silhouette-mask.png")
    source.putalpha(mask)
    art = source.crop((228, 112, 794, 888))
    art.thumbnail((290, 400), Image.Resampling.LANCZOS)
    result = Image.new("RGBA", (400, 420))
    result.alpha_composite(art, ((400 - art.width) // 2, (420 - art.height) // 2))
    result.save(root / "ear.png")
    path = (
        "M549 128 " + " ".join("C" + " ".join(f"{x} {y}" for x, y in c[1:]) for c in CURVES) + " Z"
    )
    (root / "layers.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">'
        f'<defs><clipPath id="silhouette"><path d="{path}"/></clipPath></defs>'
        '<image href="ear-source.png" width="1024" height="1024" '
        'clip-path="url(#silhouette)"/></svg>'
    )
    print(root / "ear.png")


if __name__ == "__main__":
    main()
