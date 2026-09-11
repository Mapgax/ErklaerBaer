"""Build a complete local benchmark; default uses existing PCM and makes no paid call.

--expressive opts into already authorized finite Google calls; the default is a
clearly marked cached-Chirp working render while the account gate is unresolved.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from erklaerbaer.audio import GoogleNarrator, _decode_wav, _write_wav
from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.build_identity import rendered_identity, verify_rendered_identity
from erklaerbaer.captions import save_segment_srt
from erklaerbaer.collage_guitar import CORAL, INK, paste_guitar
from erklaerbaer.config import load_settings
from erklaerbaer.expressive_speech import speech_identity, synthesize_segment
from erklaerbaer.mascot_library import MascotLibrary, rig_root
from erklaerbaer.media import mux_and_normalize, validate_media, write_checksums
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, school_font
from erklaerbaer.science_review import validate_science_review
from erklaerbaer.speech_cache import digest_json


def expressive_audio(board, settings, output, cache_only):
    samples = []
    timings = []
    durations = []
    cursor = 0.0
    rate = 48000
    for scene in board.scenes:
        start = cursor
        for segment in scene.segments:
            identity = speech_identity(segment, board.language.value)
            data, reused = synthesize_segment(settings, identity, cache_only=cache_only)
            # A modest pitch-preserving adjustment keeps the complete benchmark under 3 min.
            # Deliberate prediction pauses below retain their authored durations.
            adjusted = subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-v",
                    "error",
                    "-i",
                    "pipe:0",
                    "-af",
                    "atempo=1.06",
                    "-f",
                    "wav",
                    "pipe:1",
                ],
                input=data,
                capture_output=True,
                check=True,
            ).stdout
            pcm, sr = _decode_wav(adjusted)
            if sr != rate:
                raise ValueError("Unexpected sample rate")
            duration = len(pcm) / sr
            print(
                segment.segment_id,
                f"{duration:.2f}s",
                "cached" if reused else "generated",
                flush=True,
            )
            timings.append(
                {
                    "scene_id": scene.scene_id,
                    "segment_id": segment.segment_id,
                    "speaker": segment.speaker,
                    "text": segment.text,
                    "cache_key": digest_json(identity),
                    "start": cursor,
                    "end": cursor + duration,
                    "scene_start": cursor - start,
                }
            )
            samples += [pcm, np.zeros(round(segment.pause_after_seconds * rate), np.float32)]
            cursor += duration + segment.pause_after_seconds
        samples.append(np.zeros(round(0.45 * rate), np.float32))
        cursor += 0.45
        durations.append(cursor - start)
    _write_wav(output, np.concatenate(samples), rate)
    return {
        "schema_version": 3,
        "speech_processing": {"filter": "atempo=1.06", "prediction_pauses_unchanged": True},
        "scene_durations": durations,
        "total_seconds": cursor,
        "segments": timings,
    }


def pluck(t, *, hertz=220.0, decay=9.0, gain=0.07):
    """The band itself, at its actual 220 Hz; the drawn motion is explicitly slowed."""
    tone = sum(np.sin(2 * np.pi * hertz * k * t) / k**1.8 for k in range(1, 7))
    return tone * gain * np.exp(-t * decay) * np.minimum(1, t / 0.008)


def thud(t, *, hertz=90.0, decay=13.0, gain=0.05):
    """Cardboard taking up the vibration: low, short, no attack transient to speak of."""
    tone = np.sin(2 * np.pi * hertz * t) + 0.3 * np.sin(2 * np.pi * hertz * 2 * t)
    return tone * gain * np.exp(-t * decay) * np.minimum(1, t / 0.014)


def arrival(t, *, hertz=150.0, gain=0.045):
    """A soft low bloom for the pressure change completing its journey. Not a chime."""
    tone = np.sin(2 * np.pi * hertz * t) + 0.22 * np.sin(2 * np.pi * hertz * 1.5 * t)
    return tone * gain * np.minimum(1, t / 0.13) * np.exp(-t * 3.4)


# Four events in the whole episode. Each sits in measured silence after the last
# segment of a scene, and each names something the picture is doing at that moment.
SOUND_EVENTS = (
    ("scene-2-2", 0.45, pluck, {}),
    ("scene-3-2", 0.40, thud, {}),
    ("scene-4-2", 0.50, arrival, {}),
    ("scene-7-2", 0.55, pluck, {"gain": 0.05, "decay": 5.0}),
)


def add_sound_events(audio, timing):
    """Locally synthesized anchors. No samples, no provider call, no music bed."""
    data, rate = _decode_wav(audio.read_bytes())
    speech_peak = float(np.abs(data).max())
    placed = []
    for segment_id, seconds, shape, options in SOUND_EVENTS:
        segment = next(s for s in timing["segments"] if s["segment_id"] == segment_id)
        following = [s["start"] for s in timing["segments"] if s["start"] > segment["end"]]
        begins = segment["end"] + 0.05
        # A guard keeps the tail clear of the next speech onset, never under it.
        room = (min(following) if following else len(data) / rate) - begins - 0.03
        if room < seconds:
            raise ValueError(f"No measured silence for {segment_id}: {room:.2f}s available")
        start = round(begins * rate)
        count = min(round(seconds * rate), len(data) - start)
        tone = shape(np.arange(count) / rate, **options)
        data[start : start + count] += tone
        placed.append(
            {
                "after_segment": segment_id,
                "start_seconds": round(start / rate, 3),
                "seconds": round(count / rate, 3),
                "peak": round(float(np.abs(tone).max()), 5),
                "below_speech_db": round(
                    20 * math.log10(float(np.abs(tone).max()) / speech_peak), 1
                ),
                "silence_available_seconds": round(room, 3),
            }
        )
    _write_wav(audio, data, rate)
    return placed


def compose_thumbnail(settings, board, renderer, output_path):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expressive", action="store_true")
    parser.add_argument("--cache-only", action="store_true")
    parser.add_argument("--audio-only", action="store_true")
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root
    source = root / "storyboards/v3/karton-gitarre/nl-NL/7511ac9042e30f1e.json"
    board = Storyboard.model_validate_json(source.read_text())
    validate_science_review(board, settings)
    work = root / "build/v3/guitar"
    work.mkdir(parents=True, exist_ok=True)
    narration = work / "narration.wav"
    if args.expressive:
        timing = expressive_audio(board, settings, narration, args.cache_only)
        voice_status = (
            "Gemini narrator selected by owner; warmer bear delivery; full listening review pending"
        )
    else:
        GoogleNarrator(settings, BudgetLedger(root / "catalog/usage.json")).synthesize(
            board, narration, cache_only=True
        )
        timing = json.loads(narration.with_suffix(".timing.json").read_text())
        voice_status = (
            "Cached Chirp fallback; expressive voices blocked by Google API configuration"
        )
    (work / "narration.timing.json").write_text(
        json.dumps(timing, ensure_ascii=False, indent=2) + "\n"
    )
    if args.audio_only:
        print("Prepared narration:", timing["total_seconds"], "seconds", flush=True)
        return
    if not 90 <= timing["total_seconds"] <= 180:
        raise ValueError(f"Measured duration outside benchmark range: {timing['total_seconds']}")
    sound_events = add_sound_events(narration, timing)
    payload = rendered_identity(board, settings, narration, timing)
    fingerprint = digest_json(payload)[:24]
    output = root / f"artifacts/review-v3/guitar/{fingerprint}"
    output.mkdir(parents=True, exist_ok=True)
    if (output / "video.mp4").exists():
        print("Existing exact render:", output)
        return
    renderer = PaperCutRenderer(settings)
    renderer.render_video(
        board,
        timing["scene_durations"],
        work / "silent.mp4",
        audio_path=narration,
        segments=timing["segments"],
    )
    mux_and_normalize(work / "silent.mp4", narration, output / "video.mp4")
    save_segment_srt(timing["segments"], output / "captions.srt")
    compose_thumbnail(settings, board, renderer, output / "thumbnail.jpg")
    shutil.copy2(source, output / "storyboard.json")
    shutil.copy2(narration, output / "narration.wav")
    (output / "narration.timing.json").write_text(
        json.dumps(timing, ensure_ascii=False, indent=2) + "\n"
    )
    verify_rendered_identity(board, settings, narration, timing, payload, fingerprint)
    (output / "build-identity.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    validation = validate_media(output / "video.mp4", settings)
    report = {
        "build_hash": fingerprint,
        "technical_warnings": list(validation.warnings),
        "duration_seconds": validation.probe.duration_seconds,
        "resolution": [validation.probe.width, validation.probe.height],
        "fps": validation.probe.fps,
        "integrated_lufs": validation.loudness.integrated_lufs,
        "true_peak_dbfs": validation.loudness.true_peak_dbfs,
        "audio_sample_rate": validation.probe.audio_sample_rate,
        "voice_status": voice_status,
        "sound_events": sound_events,
        "owner_approved": False,
        "creative_gate": "incomplete",
        "remaining": [
            "Full-video listening review",
            "Animated prop Rive source and runtime",
            "Full MP4 visual inspection",
        ],
    }
    (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    write_checksums(list(output.glob("*")), output / "checksums.sha256")
    print(output, flush=True)


if __name__ == "__main__":
    main()
