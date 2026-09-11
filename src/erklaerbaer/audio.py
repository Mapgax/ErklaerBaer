from __future__ import annotations

import io
import json
import math
import re
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .budgets import BudgetLedger
from .config import Settings
from .errors import ExternalServiceError
from .models import Scene, ScenePrimitive, SoundCue, SpeechSegment, Storyboard
from .speech_cache import SpeechCache, digest_json


@dataclass(frozen=True)
class NarrationResult:
    scene_durations: tuple[float, ...]
    total_seconds: float
    character_count: int
    segments: tuple[dict, ...] = ()


class GoogleNarrator:
    def __init__(self, settings: Settings, ledger: BudgetLedger) -> None:
        self.settings = settings
        self.ledger = ledger

    def synthesize(
        self, storyboard: Storyboard, output_path: Path, *, cache_only: bool = False
    ) -> NarrationResult:
        sample_rate = int(self.settings.section("render")["audio_sample_rate"])
        tts = self.settings.section("tts")
        speaking_rate = self.settings.speaking_rate_for(storyboard.language)
        cache = SpeechCache(self.settings.project_root / "build" / "audio-cache")
        client = None
        scene_samples = []
        scene_durations = []
        timings = []
        character_count = 0
        cursor = 0.0
        for scene in storyboard.scenes:
            samples_for_scene = []
            scene_cursor = 0.0
            segments = narration_segments(scene)
            for segment in segments:
                identity = {
                    "text": segment.text,
                    "input_type": "text",
                    "cache_version": 1,
                    "language": storyboard.language.value,
                    "voice": self.settings.voice_for(storyboard.language),
                    "provider": str(tts["provider"]),
                    "sample_rate": sample_rate,
                    "encoding": "LINEAR16",
                    "speaking_rate": speaking_rate,
                }
                content = cache.read(identity)
                if content is None:
                    if cache_only or self.settings.dry_run:
                        raise ExternalServiceError(
                            "Speech segment is not cached; visual-only rerender made no paid call"
                        )
                    self.settings.required_env(
                        "GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"
                    )
                    from google.cloud import texttospeech

                    if client is None:
                        client = texttospeech.TextToSpeechClient()
                    # Claim first; any crash or timeout leaves a visible recovery gate.
                    cache.begin(identity)
                    self.ledger.reserve(
                        "tts_characters",
                        len(segment.text),
                        int(self.settings.section("budgets")["monthly_tts_characters"]),
                        dry_run=False,
                    )
                    try:
                        response = client.synthesize_speech(
                            input=texttospeech.SynthesisInput(text=segment.text),
                            voice=texttospeech.VoiceSelectionParams(
                                language_code=storyboard.language.value,
                                name=self.settings.voice_for(storyboard.language),
                            ),
                            audio_config=texttospeech.AudioConfig(
                                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                                sample_rate_hertz=sample_rate,
                                speaking_rate=speaking_rate,
                            ),
                            retry=None,
                        )
                        content = response.audio_content
                        decoded, rate = _decode_wav(content)
                        cache.save(identity, content, len(decoded) / rate)
                    except Exception as exc:
                        raise ExternalServiceError(
                            f"Text-to-Speech failed: {type(exc).__name__}; submission retained"
                        ) from exc
                    character_count += len(segment.text)
                samples, rate = _decode_wav(content)
                samples = _resample(samples, rate, sample_rate)
                speech_seconds = len(samples) / sample_rate
                timings.append(
                    {
                        "scene_id": scene.scene_id,
                        "segment_id": segment.segment_id,
                        "text": segment.text,
                        "cache_key": digest_json(identity),
                        "start": cursor + scene_cursor,
                        "end": cursor + scene_cursor + speech_seconds,
                        "scene_start": scene_cursor,
                    }
                )
                pause = np.zeros(round(segment.pause_after_seconds * sample_rate), np.float32)
                samples_for_scene.extend([samples, pause])
                scene_cursor += (len(samples) + len(pause)) / sample_rate
            tail = np.zeros(round(float(tts["scene_tail_seconds"]) * sample_rate), np.float32)
            combined_scene = np.concatenate([*samples_for_scene, tail])
            _add_sound_cue(combined_scene, scene.sound_cue, sample_rate)
            duration = len(combined_scene) / sample_rate
            scene_samples.append(combined_scene)
            scene_durations.append(duration)
            cursor += duration
        combined = np.concatenate(scene_samples)
        _write_wav(output_path, combined, sample_rate)
        result = NarrationResult(
            tuple(scene_durations), len(combined) / sample_rate, character_count, tuple(timings)
        )
        output_path.with_suffix(".timing.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "scene_durations": scene_durations,
                    "total_seconds": result.total_seconds,
                    "segments": timings,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        return result


def narration_segments(scene: Scene) -> list[SpeechSegment]:
    if scene.segments:
        return scene.segments
    sentences = re.split(r"(?<=[.!?])\s+", scene.narration.strip())
    result = [
        SpeechSegment(segment_id=f"{scene.scene_id}-{i + 1}", text=text)
        for i, text in enumerate(sentences)
    ]
    if scene.primitive is ScenePrimitive.PREDICTION:
        result[-1].pause_after_seconds = 2.5
    return result


def _speech_markup(scene: Scene) -> str:
    """Add sparse, semantic pauses without polluting captions or stored narration."""
    text = scene.narration.strip()
    if scene.primitive in {ScenePrimitive.QUESTION, ScenePrimitive.PREDICTION}:
        question_end = text.find("?")
        if 0 <= question_end < len(text) - 1:
            pause = "long" if scene.primitive is ScenePrimitive.PREDICTION else "short"
            text = text[: question_end + 1] + f" [pause {pause}]" + text[question_end + 1 :]
            return text
    if scene.primitive is ScenePrimitive.PREDICTION:
        text += " [pause long]"
    return text


def synthesize_silence(
    storyboard: Storyboard, output_path: Path, sample_rate: int = 48_000
) -> NarrationResult:
    """Offline media-test helper. It is never selected for a production upload."""
    durations = tuple(scene.duration_hint_seconds for scene in storyboard.scenes)
    samples = np.zeros(round(sum(durations) * sample_rate), dtype=np.float32)
    _write_wav(output_path, samples, sample_rate)
    return NarrationResult(
        scene_durations=durations,
        total_seconds=sum(durations),
        character_count=sum(len(scene.narration) for scene in storyboard.scenes),
    )


def audio_envelope(path: Path, fps: int, frame_count: int) -> np.ndarray:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        sample_rate = handle.getframerate()
        raw = handle.readframes(handle.getnframes())
    if sample_width != 2:
        return np.zeros(frame_count, dtype=np.float32)
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    window = max(1, round(sample_rate / fps))
    result = np.zeros(frame_count, dtype=np.float32)
    for index in range(frame_count):
        block = samples[index * window : (index + 1) * window]
        if len(block):
            result[index] = min(1.0, float(np.sqrt(np.mean(block**2))) * 7.5)
    return result


def _decode_wav(content: bytes) -> tuple[np.ndarray, int]:
    with wave.open(io.BytesIO(content), "rb") as handle:
        if handle.getsampwidth() != 2:
            raise ValueError("TTS must return 16-bit PCM")
        channels = handle.getnchannels()
        sample_rate = handle.getframerate()
        raw = handle.readframes(handle.getnframes())
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    return samples, sample_rate


def _resample(samples: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if not len(samples) or source_rate == target_rate:
        return samples
    target_length = round(len(samples) * target_rate / source_rate)
    old = np.linspace(0.0, 1.0, len(samples), endpoint=False)
    new = np.linspace(0.0, 1.0, target_length, endpoint=False)
    return np.interp(new, old, samples).astype(np.float32)


def _add_sound_cue(samples: np.ndarray, cue: SoundCue, sample_rate: int) -> None:
    if cue is SoundCue.NONE or len(samples) < sample_rate // 4:
        return
    duration = min(0.22, len(samples) / sample_rate)
    count = round(duration * sample_rate)
    time = np.arange(count, dtype=np.float32) / sample_rate
    envelope = np.sin(np.linspace(0, math.pi, count, dtype=np.float32)) ** 2
    frequencies = {
        SoundCue.CHIME: (660.0, 880.0),
        SoundCue.WHOOSH: (180.0, 420.0),
        SoundCue.POP: (240.0, 180.0),
        SoundCue.SPARKLE: (880.0, 1320.0),
    }
    start_frequency, end_frequency = frequencies[cue]
    phase = (
        2
        * math.pi
        * (start_frequency * time + 0.5 * (end_frequency - start_frequency) / duration * time**2)
    )
    tone = 0.035 * np.sin(phase) * envelope
    samples[:count] = np.clip(samples[:count] + tone, -1.0, 1.0)


def _write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def collapse_internal_silence(samples, rate, *, threshold=0.02, max_gap=0.6, guard=0.12):
    """Shorten silences *inside* one spoken segment, leaving its edges intact.

    A synthesized voice sometimes inserts long pauses of its own inside a short line. Those
    are not authored: the pauses this project designs sit between segments as
    `pause_after_seconds`, and those are never touched here. Only stretches of quiet longer
    than `max_gap` are shortened, and only between the first and last voiced sample.
    """
    if len(samples) == 0:
        return samples
    voiced = np.abs(samples) > threshold
    if not voiced.any():
        return samples
    # Treat a brief dip between words as speech, so words are never welded together.
    pad = max(1, round(guard * rate))
    kernel = np.ones(2 * pad + 1, dtype=bool)
    held = np.convolve(voiced, kernel, mode="same") > 0
    first, last = np.nonzero(held)[0][[0, -1]]
    limit = round(max_gap * rate)
    keep = np.ones(len(samples), dtype=bool)
    index = first
    while index <= last:
        if held[index]:
            index += 1
            continue
        run_end = index
        while run_end <= last and not held[run_end]:
            run_end += 1
        if run_end - index > limit:
            keep[index + limit : run_end] = False
        index = run_end
    return samples[keep]


def keep_first_utterance(samples, rate, characters, *, threshold=0.02, guard=0.25, pace=13.0):
    """Drop a repeated reading of a short line, keeping the first one.

    A synthesized voice asked for a very short sentence sometimes reads it several times.
    A repeat shows up as speech that starts again *after* the line has already been spoken,
    so anything beginning past the time the text needs is dropped. Nothing is trimmed unless
    what remains is long enough to be the whole line, so a genuine pause is never cut.
    """
    if len(samples) == 0 or characters <= 0:
        return samples
    voiced = np.abs(samples) > threshold
    if not voiced.any():
        return samples
    pad = max(1, round(guard * rate))
    held = np.convolve(voiced, np.ones(2 * pad + 1, dtype=bool), mode="same") > 0
    edges = np.diff(held.astype(np.int8))
    starts = list(np.nonzero(edges == 1)[0] + 1)
    ends = list(np.nonzero(edges == -1)[0] + 1)
    if held[0]:
        starts.insert(0, 0)
    if held[-1]:
        ends.append(len(held))
    expected = characters / pace
    kept_end = None
    for start, end in zip(starts, ends, strict=False):
        if start / rate >= expected and kept_end is not None:
            break
        kept_end = end
    if kept_end is None or kept_end >= len(samples):
        return samples
    # Refuse to shorten below what the line plausibly needs; better long than truncated.
    if kept_end / rate < expected * 0.75:
        return samples
    return samples[:kept_end]
