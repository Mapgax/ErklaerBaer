from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .models import Storyboard


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def render_srt(storyboard: Storyboard, scene_durations: Sequence[float]) -> str:
    if len(scene_durations) != len(storyboard.scenes):
        raise ValueError("One duration is required per scene")
    entries: list[str] = []
    start = 0.0
    index = 1
    for scene, duration in zip(storyboard.scenes, scene_durations, strict=True):
        if duration <= 0:
            raise ValueError("Caption durations must be positive")
        words = scene.narration.split()
        chunks = _caption_chunks(words)
        chunk_duration = duration / len(chunks)
        for chunk_index, chunk in enumerate(chunks):
            end = start + chunk_duration
            if chunk_index == len(chunks) - 1:
                end = start + chunk_duration
            entries.append(f"{index}\n{_timestamp(start)} --> {_timestamp(end)}\n{' '.join(chunk)}")
            start = end
            index += 1
    return "\n\n".join(entries) + "\n"


def _caption_chunks(words: list[str], target_words: int = 9) -> list[list[str]]:
    if not words:
        return [[]]
    chunk_count = max(1, round(len(words) / target_words))
    size = max(1, (len(words) + chunk_count - 1) // chunk_count)
    return [words[index : index + size] for index in range(0, len(words), size)]


def save_srt(storyboard: Storyboard, scene_durations: Sequence[float], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_srt(storyboard, scene_durations), encoding="utf-8")


def save_segment_srt(segments: Sequence[dict], path: Path) -> None:
    """One subtitle per measured speech segment; silent holds remain caption-free."""
    entries = []
    for index, segment in enumerate(segments, 1):
        entries.append(
            f"{index}\n{_timestamp(segment['start'])} --> {_timestamp(segment['end'])}"
            f"\n{segment['text']}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(entries) + "\n", encoding="utf-8")
