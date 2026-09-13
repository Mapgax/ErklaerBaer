"""Reusable paper/felt ident and closing card, with an original, locally synthesized jingle.

No provider calls. The combined review retains its episode's exact sealed source bundle.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from erklaerbaer.audio import _write_wav
from erklaerbaer.build_identity import sha256
from erklaerbaer.config import load_settings
from erklaerbaer.mascot_library import MascotLibrary, rig_root
from erklaerbaer.media import mux_and_normalize, validate_media, write_checksums
from erklaerbaer.renderer import PaperCutRenderer, _font, school_font
from erklaerbaer.speech_cache import digest_json

BASE_DURATION = 12
FPS = 30
RATE = 48000
# Original D-major phrase, soft wooden/bell-like synthesis; no drums or sampled music.
MELODY = [
    (0.55, 62),
    (1.18, 66),
    (1.80, 69),
    (2.74, 71),
    (3.37, 69),
    (4.30, 66),
    (4.93, 64),
    (5.55, 67),
    (6.49, 66),
    (7.12, 64),
    (8.05, 62),
]


# The outro answers the intro: the same card, the raised paw, and a farewell in place of
# the tagline. The closing phrase is the opening phrase resolving down to its tonic.
OUTRO_DURATION = 4.0
OUTRO_MELODY = [(0.30, 69), (0.92, 66), (1.54, 62)]
FAREWELL = {"nl-NL": "Tot ziens!", "de-DE": "Bis bald!"}


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def jingle(duration=BASE_DURATION):
    """The same D-major phrase. A shorter cut plays it faster; the pitches never move."""
    scale = duration / BASE_DURATION
    audio = np.zeros(round(duration * RATE), np.float64)
    for start, midi in MELODY:
        t = np.arange(round(2.1 * scale * RATE)) / RATE
        shaped = t / scale
        frequency = 440 * 2 ** ((midi - 69) / 12)
        note = (
            np.sin(2 * np.pi * frequency * t)
            + 0.24 * np.sin(2 * np.pi * frequency * 2 * t)
            + 0.08 * np.sin(2 * np.pi * frequency * 3 * t)
        )
        note *= np.minimum(1, shaped / 0.018) * np.exp(-shaped * 3.3) * 0.13
        begin = round(start * scale * RATE)
        count = min(len(note), len(audio) - begin)
        audio[begin : begin + count] += note[:count]
        # A quiet single echo lends space without a percussion track.
        echo = begin + round(0.13 * scale * RATE)
        count = min(len(note), len(audio) - echo)
        audio[echo : echo + count] += note[:count] * 0.10
    # Soft tonic underpinning for the closing note, fading completely before the episode.
    t = np.arange(round(2.0 * scale * RATE)) / RATE
    shaped = t / scale
    chord = sum(np.sin(2 * np.pi * f * t) for f in (146.8324, 184.9972, 220))
    chord *= 0.018 * np.minimum(1, shaped / 0.1) * np.exp(-2.7 * shaped)
    start = round(8.05 * scale * RATE)
    count = min(len(chord), len(audio) - start)
    audio[start : start + count] += chord[:count]
    elapsed = np.arange(len(audio)) / RATE / scale
    audio *= np.minimum(1, np.maximum(0, (10.2 - elapsed) / 0.5))
    return audio.astype(np.float32)


def outro_jingle(duration=OUTRO_DURATION):
    """Three notes of the same D-major phrase, falling to the tonic. No samples, no calls."""
    audio = np.zeros(round(duration * RATE), np.float64)
    for start, midi in OUTRO_MELODY:
        t = np.arange(round(2.1 * RATE)) / RATE
        frequency = 440 * 2 ** ((midi - 69) / 12)
        note = (
            np.sin(2 * np.pi * frequency * t)
            + 0.24 * np.sin(2 * np.pi * frequency * 2 * t)
            + 0.08 * np.sin(2 * np.pi * frequency * 3 * t)
        )
        note *= np.minimum(1, t / 0.018) * np.exp(-t * 3.3) * 0.13
        begin = round(start * RATE)
        count = min(len(note), len(audio) - begin)
        audio[begin : begin + count] += note[:count]
        echo = begin + round(0.13 * RATE)
        count = min(len(note), len(audio) - echo)
        audio[echo : echo + count] += note[:count] * 0.10
    t = np.arange(round(2.2 * RATE)) / RATE
    chord = sum(np.sin(2 * np.pi * f * t) for f in (146.8324, 184.9972, 220))
    chord *= 0.020 * np.minimum(1, t / 0.1) * np.exp(-2.2 * t)
    begin = round(1.54 * RATE)
    count = min(len(chord), len(audio) - begin)
    audio[begin : begin + count] += chord[:count]
    elapsed = np.arange(len(audio)) / RATE
    audio *= np.minimum(1, np.maximum(0, (duration - 0.35 - elapsed) / 0.5))
    return audio.astype(np.float32)


def outro_frame(seconds, backdrop, library, language, duration=OUTRO_DURATION):
    """The intro's card, answered: raised paw where the wave would be, farewell for tagline."""
    canvas = backdrop.copy().convert("RGBA")
    layer = Image.new("RGBA", canvas.size)
    d = ImageDraw.Draw(layer)
    d.ellipse((105, 120, 790, 940), fill="#fffcf3")
    d.ellipse((1620, 175, 1670, 225), fill="#34877f")
    d.ellipse((1690, 200, 1720, 230), fill="#d68462")
    # The rig has no wave; `aha` raises an open paw, which is the honest closest thing.
    bear = library.frame("aha", min(1.75, seconds * 0.9), 735).copy()
    bear.putalpha(bear.getchannel("A").point(lambda a: round(a * ease((seconds - 0.2) / 0.8))))
    layer.alpha_composite(bear, (180, 150))
    title = Image.new("RGBA", canvas.size)
    ImageDraw.Draw(title).text(
        (805, 335), "ErklaerBaer", font=_font(112, bold=True), fill="#344744"
    )
    title.putalpha(title.getchannel("A").point(lambda a: round(a * ease((seconds - 0.9) / 0.8))))
    layer.alpha_composite(title)
    bye = Image.new("RGBA", canvas.size)
    bd = ImageDraw.Draw(bye)
    bd.text(
        (810, 495),
        FAREWELL[language],
        font=school_font(84),
        fill="#34877f",
        stroke_width=1,
        stroke_fill="#34877f",
    )
    bd.line((812, 645, 1090, 645), fill="#d68462", width=5)
    bye.putalpha(bye.getchannel("A").point(lambda a: round(a * ease((seconds - 1.7) / 0.8))))
    layer.alpha_composite(bye)
    opacity = ease(seconds / 0.4) * (1 - ease((seconds - (duration - 0.9)) / 0.8))
    layer.putalpha(layer.getchannel("A").point(lambda a: round(a * opacity)))
    canvas.alpha_composite(layer)
    return canvas.convert("RGB")


def frame(seconds, backdrop, library, language, duration=BASE_DURATION):
    seconds = seconds / (duration / BASE_DURATION)
    canvas = backdrop.copy().convert("RGBA")
    layer = Image.new("RGBA", canvas.size)
    d = ImageDraw.Draw(layer)
    d.ellipse((105, 120, 790, 940), fill="#fffcf3")
    # A few static cut-paper circles keep the visual language quiet and tactile.
    d.ellipse((1620, 175, 1670, 225), fill="#34877f")
    d.ellipse((1690, 200, 1720, 230), fill="#d68462")
    # Frames are cached by the library; fade a copy so later loops retain their alpha.
    bear = library.frame("neutral", seconds, 735).copy()
    bear.putalpha(bear.getchannel("A").point(lambda a: round(a * ease((seconds - 0.25) / 1.0))))
    layer.alpha_composite(bear, (180, 150))
    title = Image.new("RGBA", canvas.size)
    td = ImageDraw.Draw(title)
    title_y = round(335 + 16 * (1 - ease((seconds - 1) / 1.0)))
    td.text((805, title_y), "ErklaerBaer", font=_font(112, bold=True), fill="#344744")
    title.putalpha(title.getchannel("A").point(lambda a: round(a * ease((seconds - 1) / 1.0))))
    layer.alpha_composite(title)
    subtitle = Image.new("RGBA", canvas.size)
    sd = ImageDraw.Draw(subtitle)
    text = (
        "Kleine vragen.\nGrote ontdekkingen."
        if language == "nl-NL"
        else "Kleine Fragen.\nGroße Entdeckungen."
    )
    sd.multiline_text((810, 495), text, font=_font(58, bold=False), fill="#34877f", spacing=18)
    sd.line((812, 675, 1090, 675), fill="#d68462", width=5)
    subtitle.putalpha(
        subtitle.getchannel("A").point(lambda a: round(a * ease((seconds - 2.3) / 1.0)))
    )
    layer.alpha_composite(subtitle)
    opacity = ease(seconds / 0.5) * (1 - ease((seconds - 10.8) / 1.2))
    layer.putalpha(layer.getchannel("A").point(lambda a: round(a * opacity)))
    canvas.alpha_composite(layer)
    return canvas.convert("RGB")


def shift_srt(source, seconds):
    import re

    def shift(match):
        h, m, s, ms = map(int, match.groups())
        value = ((h * 60 + m) * 60 + s) * 1000 + ms + round(seconds * 1000)
        h, value = divmod(value, 3600000)
        m, value = divmod(value, 60000)
        s, ms = divmod(value, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    return re.sub(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", shift, source)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", type=Path, required=True)
    parser.add_argument("--language", choices=["nl-NL", "de-DE"], default="nl-NL")
    parser.add_argument("--duration", type=float, default=BASE_DURATION)
    parser.add_argument("--outro-duration", type=float, default=OUTRO_DURATION)
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root
    library = MascotLibrary(rig_root(root))
    board = json.loads((args.episode / "storyboard.json").read_text())
    from erklaerbaer.models import Storyboard

    renderer = PaperCutRenderer(settings)
    storyboard = Storyboard.model_validate(board)
    backdrop = renderer.render_background(storyboard, progress=0)
    identity = {
        "source_sha256": sha256(Path(__file__)),
        "language": args.language,
        # A clip-baked library has no Rive runtime; its manifest digest below identifies it.
        "mascot": library.manifest.get("runtime", {}).get("sha256"),
        "episode_sha256": sha256(args.episode / "video.mp4"),
        "duration": args.duration,
        "outro_duration": args.outro_duration,
        "mascot_manifest": digest_json(library.manifest),
        "renderer_sha256": sha256(root / "src/erklaerbaer/renderer.py"),
    }
    key = digest_json(identity)[:24]
    out = root / "artifacts/review-v3/intro" / key
    out.mkdir(parents=True, exist_ok=True)
    if not (out / "intro.mp4").exists():
        wav = out / "jingle.wav"
        _write_wav(wav, jingle(args.duration), RATE)
        with imageio.get_writer(
            out / "silent.mp4",
            fps=FPS,
            codec="libx264",
            pixelformat="yuv420p",
            macro_block_size=1,
            ffmpeg_params=["-crf", "18", "-preset", "medium"],
        ) as writer:
            for i in range(round(args.duration * FPS)):
                writer.append_data(
                    np.asarray(frame(i / FPS, backdrop, library, args.language, args.duration))
                )
        mux_and_normalize(out / "silent.mp4", wav, out / "intro.mp4")
        frame(args.duration / 3, backdrop, library, args.language, args.duration).save(
            out / "thumbnail.jpg", quality=92
        )
    if not (out / "outro.mp4").exists():
        wav = out / "outro-jingle.wav"
        _write_wav(wav, outro_jingle(args.outro_duration), RATE)
        with imageio.get_writer(
            out / "outro-silent.mp4",
            fps=FPS,
            codec="libx264",
            pixelformat="yuv420p",
            macro_block_size=1,
            ffmpeg_params=["-crf", "18", "-preset", "medium"],
        ) as writer:
            for i in range(round(args.outro_duration * FPS)):
                writer.append_data(
                    np.asarray(
                        outro_frame(i / FPS, backdrop, library, args.language, args.outro_duration)
                    )
                )
        mux_and_normalize(out / "outro-silent.mp4", wav, out / "outro.mp4")
    combined = out / "full-review.mp4"
    if not combined.exists():
        subprocess.run(
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-y",
                "-v",
                "error",
                "-i",
                str(out / "intro.mp4"),
                "-i",
                str(args.episode / "video.mp4"),
                "-i",
                str(out / "outro.mp4"),
                "-filter_complex",
                "[0:v:0][0:a:0][1:v:0][1:a:0][2:v:0][2:a:0]concat=n=3:v=1:a=1[v][a]",
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-preset",
                "medium",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(combined),
            ],
            check=True,
        )
    (out / "captions.srt").write_text(
        shift_srt((args.episode / "captions.srt").read_text(), args.duration)
    )
    media = validate_media(combined, settings)
    identity.update(
        duration_seconds=media.probe.duration_seconds,
        integrated_lufs=media.loudness.integrated_lufs,
        true_peak_dbfs=media.loudness.true_peak_dbfs,
        warnings=list(media.warnings),
        melody=MELODY,
        jingle_provenance="Original local additive synthesis; no samples or provider calls",
        episode_build=args.episode.name,
        owner_approved=False,
    )
    (out / "manifest.json").write_text(json.dumps(identity, indent=2) + "\n")
    write_checksums(
        [
            out / n
            for n in [
                "intro.mp4",
                "outro.mp4",
                "full-review.mp4",
                "jingle.wav",
                "outro-jingle.wav",
                "captions.srt",
                "thumbnail.jpg",
                "manifest.json",
            ]
        ],
        out / "checksums.sha256",
    )
    print(out, flush=True)


if __name__ == "__main__":
    main()
