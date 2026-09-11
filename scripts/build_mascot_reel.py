"""Build a labelled six-action reel at the production 1920x1080 frame size."""

from __future__ import annotations

import argparse

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw

from erklaerbaer.config import load_settings
from erklaerbaer.mascot_library import MascotLibrary
from erklaerbaer.renderer import Palette, _centered_multiline, _font


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--library", default="assets/mascot/rig/v2")
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root / args.library
    library = MascotLibrary(root)
    output = (
        settings.project_root / "artifacts/review-v2/six-action-reel.mp4"
        if args.output is None
        else settings.project_root / args.output
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fps = 30
    palette = Palette()
    writer = imageio.get_writer(
        output,
        fps=fps,
        codec="libx264",
        format="FFMPEG",
        pixelformat="yuv420p",
        macro_block_size=1,
        ffmpeg_params=["-crf", "18", "-preset", "medium", "-movflags", "+faststart"],
    )
    try:
        for action, spec in library.manifest["actions"].items():
            seconds = max(float(spec["duration"]), 2.0)
            for index in range(round(seconds * fps)):
                frame = Image.new("RGB", (1920, 1080), palette.cream)
                draw = ImageDraw.Draw(frame)
                draw.rounded_rectangle((100, 80, 1820, 1000), 48, fill=palette.white)
                clip = library.frame(action, index / fps, 760)
                frame.paste(clip, ((1920 - clip.width) // 2, 220), clip)
                label = f"{action.upper()}  /  {spec['behavior']}  /  {spec['duration']:.1f} s"
                _centered_multiline(
                    draw,
                    label,
                    (160, 105, 1760, 215),
                    _font(50, bold=True),
                    palette.ink,
                    spacing=5,
                )
                writer.append_data(np.asarray(frame, dtype=np.uint8))
    finally:
        writer.close()
    print(output)


if __name__ == "__main__":
    main()
