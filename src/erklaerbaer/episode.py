"""Build one v3 episode: measured speech, sound anchors, render, captions, sealed identity.

Every episode goes through this one path. What differs between episodes is data, kept in
`episodes.py`: how a raw take is tidied, where the sound anchors sit, and the thumbnail.
Speech is the only paid step, and it is journalled by `synthesize_segment`.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import imageio_ffmpeg
import numpy as np

from .audio import _decode_wav, _write_wav, collapse_internal_silence, keep_first_utterance
from .build_identity import rendered_identity, verify_rendered_identity
from .captions import save_segment_srt
from .config import Settings
from .expressive_speech import SHORT_LINE_CHARACTERS, speech_identity, synthesize_segment
from .media import mux_and_normalize, validate_media, write_checksums
from .models import Storyboard
from .renderer import PaperCutRenderer
from .science_review import validate_science_review
from .speech_cache import digest_json

RATE = 48000
TEMPO = "atempo=1.06"
SCENE_GAP_SECONDS = 0.45
DURATION_RANGE = (90.0, 180.0)
# Full single readings measured 9.6 to 17.8 characters per voiced second; a line read twice
# or more comes in well under this.
REPEAT_CHARACTERS_PER_SECOND = 8.5
VOICED_THRESHOLD = 0.02
SEALED = "checksums.sha256"
# A guard keeps an anchor's tail clear of the next speech onset, never under it.
ONSET_GUARD_SECONDS = 0.03


@dataclass(frozen=True)
class TakeCleanup:
    """How a raw synthesized take is tidied before it is placed on the timeline.

    trim_repeats: "short-lines" keeps only the first reading of every short line;
    "slow-short-lines" does so only when the take is too slow for its text to be one reading.
    """

    collapse_pauses: bool = False
    trim_repeats: Literal["never", "short-lines", "slow-short-lines"] = "never"
    edge_silence: float | None = None


@dataclass(frozen=True)
class SoundEvent:
    """A local sound placed `offset` seconds after a segment ends, lasting `seconds`."""

    segment_id: str
    offset: float
    seconds: float
    shape: Callable[..., np.ndarray]
    options: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class EpisodeSpec:
    """Everything that makes one episode different from another."""

    name: str
    storyboard: str
    takes: TakeCleanup
    sound_events: tuple[SoundEvent, ...]
    thumbnail: Callable[[Settings, Storyboard, PaperCutRenderer, Path], None]
    # Anchors must sit this many dB under the speech peak; None only for published episodes
    # built before the rule was enforced.
    anchor_band: tuple[float, float] | None = (-25.0, -20.0)


def voiced_seconds(pcm: np.ndarray, rate: int) -> float:
    window = int(0.01 * rate)
    count = len(pcm) // window
    if count == 0:
        return 1e-3
    loud = np.abs(pcm[: count * window]).reshape(count, window).max(axis=1) > VOICED_THRESHOLD
    return max(1e-3, loud.sum() * 0.01)


def trim_edges(pcm: np.ndarray, rate: int, keep: float) -> np.ndarray:
    """Leave at most `keep` seconds of quiet before the first and after the last voiced sample."""
    loud = np.nonzero(np.abs(pcm) > VOICED_THRESHOLD)[0]
    if len(loud) == 0:
        return pcm
    pad = round(keep * rate)
    return pcm[max(0, loud[0] - pad) : min(len(pcm), loud[-1] + pad)]


def tidy_take(pcm: np.ndarray, rate: int, text: str, cleanup: TakeCleanup) -> np.ndarray:
    if cleanup.collapse_pauses:
        # The voice sometimes pauses at length inside a line. Authored pauses sit between
        # segments and are untouched; these are not authored.
        pcm = collapse_internal_silence(pcm, rate)
    if len(text) < SHORT_LINE_CHARACTERS and cleanup.trim_repeats != "never":
        # A short line is where the voice sometimes reads twice. A single reading with long
        # pauses looks the same to the trimmer, so the stricter policy only trims a take that
        # is too slow for its text; the Dutch pilot's lines were cut mid-sentence otherwise.
        slow = len(text) / voiced_seconds(pcm, rate) < REPEAT_CHARACTERS_PER_SECOND
        if cleanup.trim_repeats == "short-lines" or slow:
            pcm = keep_first_utterance(pcm, rate, len(text))
    if cleanup.edge_silence is not None:
        pcm = trim_edges(pcm, rate, cleanup.edge_silence)
    return pcm


def _tempo(wav: bytes) -> bytes:
    """A modest pitch-preserving adjustment; authored pauses keep their durations."""
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", "pipe:0"]
    command += ["-af", TEMPO, "-f", "wav", "pipe:1"]
    return subprocess.run(command, input=wav, capture_output=True, check=True).stdout


def assemble_narration(
    board: Storyboard,
    settings: Settings,
    output: Path,
    *,
    cleanup: TakeCleanup,
    cache_only: bool,
    retry_failed: bool = False,
) -> dict:
    """Speak every segment (from cache where possible) and write measured timings."""
    samples, timings, durations = [], [], []
    cursor = 0.0
    for scene in board.scenes:
        start = cursor
        for segment in scene.segments:
            identity = speech_identity(segment, board.language.value)
            data, reused = synthesize_segment(
                settings, identity, cache_only=cache_only, retry_rejected=retry_failed
            )
            pcm, rate = _decode_wav(_tempo(data))
            if rate != RATE:
                raise ValueError(f"{segment.segment_id}: unexpected sample rate {rate}")
            pcm = tidy_take(pcm, rate, segment.text, cleanup)
            duration = len(pcm) / rate
            print(segment.segment_id, f"{duration:.2f}s", "cached" if reused else "generated")
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
            samples += [pcm, np.zeros(round(segment.pause_after_seconds * RATE), np.float32)]
            cursor += duration + segment.pause_after_seconds
        samples.append(np.zeros(round(SCENE_GAP_SECONDS * RATE), np.float32))
        cursor += SCENE_GAP_SECONDS
        durations.append(cursor - start)
    _write_wav(output, np.concatenate(samples), RATE)
    return {
        "schema_version": 3,
        "speech_processing": {"filter": TEMPO, "prediction_pauses_unchanged": True},
        "scene_durations": durations,
        "total_seconds": cursor,
        "segments": timings,
    }


# Full single readings of both voices measured 9.6 to 17.8 characters per voiced second.
SINGLE_READING_RATE = (9.0, 18.5)


def reading_rates(audio: Path, timing: dict) -> list[tuple[str, float]]:
    """Characters per voiced second of every placed take, to catch a cut or repeated reading.

    Too fast means speech was trimmed away; too slow means the voice said more than the text.
    Run it on narration before sound anchors are mixed in.
    """
    data, rate = _decode_wav(audio.read_bytes())
    rates = []
    for segment in timing["segments"]:
        take = data[round(segment["start"] * rate) : round(segment["end"] * rate)]
        rates.append((segment["segment_id"], len(segment["text"]) / voiced_seconds(take, rate)))
    return rates


def synthetic_timing(board: Storyboard, min_segment_seconds: float) -> dict:
    """Timings in the measured format, estimated from characters, for stills before speech."""
    durations, segments, cursor = [], [], 0.0
    for scene in board.scenes:
        start = cursor
        for segment in scene.segments:
            seconds = max(min_segment_seconds, len(segment.text) / 15.0)
            segments.append(
                {
                    "scene_id": scene.scene_id,
                    "segment_id": segment.segment_id,
                    "start": cursor,
                    "end": cursor + seconds,
                    "scene_start": cursor - start,
                }
            )
            cursor += seconds + segment.pause_after_seconds
        cursor += SCENE_GAP_SECONDS
        durations.append(cursor - start)
    return {"scene_durations": durations, "segments": segments}


def mix_sound_events(
    audio: Path,
    timing: dict,
    events: tuple[SoundEvent, ...],
    *,
    band: tuple[float, float] | None,
) -> list[dict]:
    """Add each anchor in measured silence; refuse one that would sit under speech."""
    data, rate = _decode_wav(audio.read_bytes())
    speech_peak = float(np.abs(data).max())
    by_id = {s["segment_id"]: s for s in timing["segments"]}
    placed = []
    for event in events:
        segment = by_id.get(event.segment_id)
        if segment is None:
            raise ValueError(f"Sound anchor names unknown segment {event.segment_id}")
        following = [s["start"] for s in timing["segments"] if s["start"] > segment["end"]]
        begins = segment["end"] + event.offset
        room = (min(following) if following else len(data) / rate) - begins
        room -= ONSET_GUARD_SECONDS
        if room < event.seconds:
            raise ValueError(f"No measured silence for {event.segment_id}: {room:.2f}s available")
        start = round(begins * rate)
        count = min(round(event.seconds * rate), len(data) - start)
        tone = event.shape(np.arange(count) / rate, **event.options)
        below = 20 * math.log10(float(np.abs(tone).max()) / speech_peak)
        if band is not None and not band[0] <= below <= band[1]:
            raise ValueError(f"{event.segment_id}: anchor sits {below:.1f} dB under speech")
        data[start : start + count] += tone
        placed.append(
            {
                "after_segment": event.segment_id,
                "start_seconds": round(start / rate, 3),
                "seconds": round(count / rate, 3),
                "peak": round(float(np.abs(tone).max()), 5),
                "below_speech_db": round(below, 1),
                "silence_available_seconds": round(room, 3),
            }
        )
    _write_wav(audio, data, rate)
    return placed


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def build_episode(
    settings: Settings,
    spec: EpisodeSpec,
    *,
    cache_only: bool,
    audio_only: bool = False,
    retry_failed: bool = False,
) -> Path | None:
    """Return the sealed episode folder, or None when only narration was prepared."""
    root = settings.project_root
    source = root / spec.storyboard
    board = Storyboard.model_validate_json(source.read_text())
    validate_science_review(board, settings)
    work = root / "build/v3" / spec.name
    work.mkdir(parents=True, exist_ok=True)
    narration = work / "narration.wav"
    timing = assemble_narration(
        board,
        settings,
        narration,
        cleanup=spec.takes,
        cache_only=cache_only,
        retry_failed=retry_failed,
    )
    _write_json(work / "narration.timing.json", timing)
    if audio_only:
        print("Prepared narration:", timing["total_seconds"], "seconds")
        return None
    low, high = DURATION_RANGE
    if not low <= timing["total_seconds"] <= high:
        raise ValueError(f"Measured duration outside {low}-{high} s: {timing['total_seconds']}")
    sound_events = mix_sound_events(narration, timing, spec.sound_events, band=spec.anchor_band)
    payload = rendered_identity(board, settings, narration, timing)
    fingerprint = digest_json(payload)[:24]
    output = root / "artifacts/review-v3" / spec.name / fingerprint
    # Checksums are written last, so only a folder that has them is a finished build. Anything
    # else is what an interrupted or refused run left behind, and is rebuilt from scratch.
    if (output / SEALED).exists():
        print("Existing exact render:", output)
        return output
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
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
    spec.thumbnail(settings, board, renderer, output / "thumbnail.jpg")
    shutil.copy2(source, output / "storyboard.json")
    shutil.copy2(narration, output / "narration.wav")
    _write_json(output / "narration.timing.json", timing)
    verify_rendered_identity(board, settings, narration, timing, payload, fingerprint)
    _write_json(output / "build-identity.json", payload)
    validation = validate_media(output / "video.mp4", settings)
    _write_json(
        output / "validation.json",
        {
            "build_hash": fingerprint,
            "technical_warnings": list(validation.warnings),
            "duration_seconds": validation.probe.duration_seconds,
            "resolution": [validation.probe.width, validation.probe.height],
            "fps": validation.probe.fps,
            "integrated_lufs": validation.loudness.integrated_lufs,
            "true_peak_dbfs": validation.loudness.true_peak_dbfs,
            "audio_sample_rate": validation.probe.audio_sample_rate,
            "sound_events": sound_events,
            "anchor_band_db": spec.anchor_band,
            "owner_approved": False,
            "creative_gate": "incomplete",
            "remaining": ["Full-video listening review", "Owner creative acceptance"],
        },
    )
    write_checksums(list(output.glob("*")), output / SEALED)
    return output
