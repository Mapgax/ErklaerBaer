"""A review cut is an episode wrapped in the brand bookends. Shared by upload and finalize."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import Storyboard


@dataclass(frozen=True)
class ReviewCut:
    folder: Path
    manifest: dict
    episode_folder: Path
    board: Storyboard

    @property
    def episode_build(self) -> str:
        return self.manifest["episode_build"]

    @property
    def video(self) -> Path:
        return self.folder / "full-review.mp4"

    @property
    def captions(self) -> Path:
        return self.folder / "captions.srt"

    @property
    def thumbnail(self) -> Path:
        """The episode's composed thumbnail; the intro frame only if the episode has none."""
        composed = self.episode_folder / "thumbnail.jpg"
        return composed if composed.exists() else self.folder / "thumbnail.jpg"

    @property
    def marker_build(self) -> str:
        # Two cuts of one episode must not share an identity, or a re-run recovers the wrong one.
        return f"{self.episode_build}|{self.folder.name}"

    def record_path(self, root: Path) -> Path:
        """One evidence file per cut, so an upload never overwrites an earlier one's record."""
        return root / f"artifacts/review-v3/uploads/{self.episode_build}-{self.folder.name}.json"


def load_cut(root: Path, folder: Path) -> ReviewCut:
    manifest = json.loads((folder / "manifest.json").read_text())
    episode = manifest["episode_build"]
    # The cut names its episode; the episode may live under any template's folder.
    matches = list((root / "artifacts/review-v3").glob(f"*/{episode}"))
    if len(matches) != 1:
        raise SystemExit(f"Expected one episode folder for {episode}, found {matches}")
    board = Storyboard.model_validate_json((matches[0] / "storyboard.json").read_text())
    return ReviewCut(folder, manifest, matches[0], board)


def write_record(path: Path, evidence: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=1) + "\n")
    print(json.dumps(evidence, indent=1))
