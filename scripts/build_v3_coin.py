"""Build the German coin episode. Speech is the only paid step and it is journalled.

The expressive path uses the Gemini voices the owner accepted for the guitar. Every
segment is cached, so a repeat build makes no call at all.
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

from erklaerbaer.audio import (
    GoogleNarrator,
    _decode_wav,
    _write_wav,
    collapse_internal_silence,
    keep_first_utterance,
)
from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.build_identity import rendered_identity, verify_rendered_identity
from erklaerbaer.captions import save_segment_srt
from erklaerbaer.collage_coin import (
    View,
    draw_bottle,
    draw_gas,
    draw_hands,
    draw_lid,
    gas_points,
    travelled,
)
from erklaerbaer.collage_guitar import CORAL, INK
from erklaerbaer.config import load_settings
from erklaerbaer.expressive_speech import (
    SHORT_LINE_CHARACTERS,
    speech_identity,
    synthesize_segment,
)
from erklaerbaer.mascot_library import MascotLibrary, rig_root
from erklaerbaer.media import mux_and_normalize, validate_media, write_checksums
from erklaerbaer.models import Storyboard
from erklaerbaer.renderer import PaperCutRenderer, school_font
from erklaerbaer.science_review import validate_science_review
from erklaerbaer.speech_cache import digest_json


def expressive_audio(board, settings, output, cache_only, retry_failed=False):
    samples = []
    timings = []
    durations = []
    cursor = 0.0
    rate = 48000
    for scene in board.scenes:
        start = cursor
        for segment in scene.segments:
            identity = speech_identity(segment, board.language.value)
            data, reused = synthesize_segment(
                settings, identity, cache_only=cache_only, retry_rejected=retry_failed
            )
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
            # The voice sometimes pauses at length inside a short line. Authored pauses sit
            # between segments and are untouched; these are not authored.
            pcm = collapse_internal_silence(pcm, sr)
            if len(segment.text) < SHORT_LINE_CHARACTERS:
                # Short lines are where the voice sometimes reads twice; keep the first.
                pcm = keep_first_utterance(pcm, sr, len(segment.text))
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


def clack(t, *, hertz=2100.0, decay=52.0, gain=0.05):
    """Metal on glass: a bright, very short transient with no tail to speak of."""
    tone = (
        np.sin(2 * np.pi * hertz * t)
        + 0.6 * np.sin(2 * np.pi * hertz * 1.63 * t)
        + 0.3 * np.sin(2 * np.pi * hertz * 2.41 * t)
    )
    return tone * gain * np.exp(-t * decay) * np.minimum(1, t / 0.001)


def settle(t, *, hertz=1700.0, decay=34.0, gain=0.038):
    """The coin dropping back onto the mouth: lower and softer than the lift."""
    tone = np.sin(2 * np.pi * hertz * t) + 0.45 * np.sin(2 * np.pi * hertz * 1.5 * t)
    return tone * gain * np.exp(-t * decay) * np.minimum(1, t / 0.0015)


def escape(t, *, gain=0.055):
    """Air leaving through the gap. Filtered noise, because that is what escaping air is."""
    generator = np.random.default_rng(4211)
    noise = generator.standard_normal(len(t))
    smoothed = np.convolve(noise, np.ones(48) / 48, mode="same")
    return smoothed * gain * np.minimum(1, t / 0.05) * np.exp(-t * 5.5)


# Four events in the episode, each on a beat where the picture does that exact thing.
SOUND_EVENTS = (
    ("scene-1-3", 0.30, clack, {}),
    ("scene-6-1", 0.32, clack, {"gain": 0.045}),
    ("scene-6-2", 0.55, escape, {}),
    ("scene-7-1", 0.35, settle, {}),
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


def draw_coin_thumbnail(art):
    """The bottle mid-lift: the one moment the whole episode is about."""
    view = View("lift")
    draw_bottle(view, art, warm=1.0)
    draw_hands(view, art, 1.0)
    draw_gas(view, art, gas_points(view, travelled(2.4, 1.0)), halo=1.0)
    draw_lid(view, art, lift=34 * view.scale, tilt=-5)


def compose_thumbnail(settings, board, renderer, output_path):
    """A composed still, not a frame grab: it has to survive a small feed tile."""
    stage = renderer.render_background(board, progress=0.0).convert("RGBA")
    art = Image.new("RGBA", stage.size)
    # The band is held at full pluck displacement, so it reads as a bent line.
    draw_coin_thumbnail(art)
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
    # Explicit and operator-driven: one retry of a failure the journal recorded.
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root
    source = root / "storyboards/v3/springende-muenze/de-DE/0d6d2f1d3eb3b75d.json"
    board = Storyboard.model_validate_json(source.read_text())
    validate_science_review(board, settings)
    work = root / "build/v3/coin"
    work.mkdir(parents=True, exist_ok=True)
    narration = work / "narration.wav"
    if args.expressive:
        timing = expressive_audio(
            board, settings, narration, args.cache_only, retry_failed=args.retry_failed
        )
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
    output = root / f"artifacts/review-v3/coin/{fingerprint}"
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
