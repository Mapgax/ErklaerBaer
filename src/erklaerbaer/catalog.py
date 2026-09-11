from __future__ import annotations

import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

from .models import Catalog, Language, ReleaseRecord, VideoRecord, VideoStatus, video_key

ALLOWED_TRANSITIONS: dict[VideoStatus, set[VideoStatus]] = {
    VideoStatus.STORYBOARDED: {VideoStatus.RENDERED, VideoStatus.FAILED},
    VideoStatus.RENDERED: {VideoStatus.PRIVATE, VideoStatus.FAILED},
    VideoStatus.PRIVATE: {VideoStatus.UNLISTED, VideoStatus.FAILED},
    VideoStatus.UNLISTED: {VideoStatus.PRIVATE, VideoStatus.PUBLIC, VideoStatus.FAILED},
    VideoStatus.PUBLIC: {VideoStatus.PUBLIC},
    VideoStatus.FAILED: {VideoStatus.STORYBOARDED},
}


class CatalogStore:
    """Small JSON catalog with atomic, deterministic writes."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Catalog:
        if not self.path.exists():
            return Catalog()
        return Catalog.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, catalog: Catalog) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = catalog.model_dump_json(indent=2, exclude_none=True) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            delete=False,
        ) as handle:
            handle.write(payload)
            temporary_path = Path(handle.name)
        temporary_path.replace(self.path)

    def find(
        self,
        experiment_id: str,
        language: Language,
        source_hash: str,
    ) -> VideoRecord | None:
        catalog = self.load()
        base = video_key(experiment_id, language, source_hash)
        return catalog.videos.get(catalog.current_builds.get(base, base))

    def upsert(self, record: VideoRecord) -> VideoRecord:
        record.updated_at = datetime.now(UTC)
        catalog = self.load()
        old = catalog.videos.get(record.key)
        if old and old.youtube_id and record.youtube_id != old.youtube_id:
            raise ValueError("Cannot overwrite an uploaded build")
        catalog.videos[record.key] = record
        if record.build_hash:
            base = video_key(record.experiment_id, record.language, record.source_hash)
            catalog.current_builds[base] = record.key
        self.save(catalog)
        return record

    def release_for(self, scheduled_date: date) -> ReleaseRecord | None:
        return self.load().releases.get(scheduled_date.isoformat())

    def record_release(self, release: ReleaseRecord) -> ReleaseRecord:
        catalog = self.load()
        key = release.date.isoformat()
        existing = catalog.releases.get(key)
        if existing and existing.video_key != release.video_key:
            raise ValueError(f"Date {key} is already bound to a different published video version")
        catalog.releases[key] = release
        self.save(catalog)
        return release

    def transition(
        self,
        experiment_id: str,
        language: Language,
        source_hash: str,
        status: VideoStatus,
        **updates: object,
    ) -> VideoRecord:
        record = self.find(experiment_id, language, source_hash)
        if record is None:
            raise KeyError(video_key(experiment_id, language, source_hash))
        if status is not record.status and status not in ALLOWED_TRANSITIONS[record.status]:
            raise ValueError(f"Invalid state transition: {record.status.value} -> {status.value}")
        updated = record.model_copy(update={"status": status, **updates})
        return self.upsert(updated)
