"""Decode a finished episode and lay its shots out for inspection.

Frames come from the encoded MP4, not from the renderer, so what is inspected is
what a viewer actually receives. Sampling frames is not a full viewing.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

from erklaerbaer.renderer import _font


def grab(video: Path, seconds: float) -> Image.Image:
    frame = subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-v",
            "error",
            "-ss",
            f"{seconds}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-f",
            "image2",
            "-vcodec",
            "png",
            "pipe:1",
        ],
        capture_output=True,
        check=True,
    ).stdout
    return Image.open(io.BytesIO(frame)).convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--fraction", type=float, default=0.4)
    args = parser.parse_args()
    timing = json.loads((args.bundle / "narration.timing.json").read_text())
    video = args.bundle / "video.mp4"
    out = Path("build/v3/mp4-qa") / args.bundle.name
    out.mkdir(parents=True, exist_ok=True)

    moments = []
    started = 0.0
    for index, duration in enumerate(timing["scene_durations"], start=1):
        moments.append((index, started + duration * args.fraction))
        started += duration

    cell = (640, 360)
    sheet = Image.new("RGB", (cell[0] * 2, (cell[1] + 30) * ((len(moments) + 1) // 2)), "#f6f1e4")
    draw = ImageDraw.Draw(sheet)
    label = _font(20, bold=True)
    for position, (index, seconds) in enumerate(moments):
        frame = grab(video, seconds)
        frame.save(out / f"scene-{index}.png")
        box = (position % 2 * cell[0], position // 2 * (cell[1] + 30) + 26)
        sheet.paste(frame.resize(cell, Image.Resampling.LANCZOS), box)
        draw.text(
            (box[0] + 8, box[1] - 22), f"scene {index}   {seconds:.2f}s", font=label, fill="#344744"
        )
    sheet.save(out / "shots.jpg", quality=90)
    print(out / "shots.jpg")


if __name__ == "__main__":
    main()
