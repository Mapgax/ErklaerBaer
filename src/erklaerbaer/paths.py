from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import Language


@dataclass(frozen=True)
class BundlePaths:
    root: Path
    storyboard: Path
    narration: Path
    captions: Path
    silent_video: Path
    video: Path
    thumbnail: Path
    checksum: Path


def bundle_paths(
    project_root: Path,
    experiment_id: str,
    language: Language,
    source_hash: str,
    build_hash: str | None = None,
) -> BundlePaths:
    root = project_root / "build" / experiment_id / language.value / source_hash
    artifact_root = project_root / "artifacts" / experiment_id / language.value / source_hash
    storyboard = (
        project_root / "storyboards" / experiment_id / language.value / f"{source_hash}.json"
    )
    if build_hash:
        root = root / build_hash
        artifact_root = artifact_root / build_hash
        storyboard = artifact_root / "storyboard.json"
    return BundlePaths(
        root=root,
        storyboard=storyboard,
        narration=root / "narration.wav",
        captions=artifact_root / "captions.srt",
        silent_video=root / "silent.mp4",
        video=root / "video.mp4",
        thumbnail=artifact_root / "thumbnail.jpg",
        checksum=artifact_root / "checksums.sha256",
    )
