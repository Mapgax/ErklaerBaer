from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .audio import GoogleNarrator
from .budgets import BudgetLedger
from .build_identity import build_fingerprint, require_asset_approval
from .captions import save_segment_srt
from .catalog import CatalogStore
from .config import Settings
from .errors import ExternalServiceError, SourceError
from .media import mux_and_normalize, sha256_file, validate_media, write_checksums
from .models import (
    ExperimentSnapshot,
    Language,
    ReleaseRecord,
    Storyboard,
    VideoRecord,
    VideoStatus,
    video_key,
)
from .paths import BundlePaths, bundle_paths
from .renderer import PaperCutRenderer
from .science_review import validate_science_review
from .source import MintSource
from .storyboards import StoryboardGenerator, load_storyboard, save_storyboard
from .youtube import YouTubeClient


@dataclass(frozen=True)
class BuildOutcome:
    record: VideoRecord
    paths: BundlePaths
    reused: bool


@dataclass(frozen=True)
class ReleaseOutcome:
    action: str
    language: Language
    youtube_id: str | None
    detail: str


class VideoPipeline:
    def __init__(
        self,
        settings: Settings,
        *,
        source: MintSource | None = None,
        youtube: YouTubeClient | None = None,
    ) -> None:
        self.settings = settings
        self.source = source or MintSource(settings)
        self.catalog = CatalogStore(settings.project_root / "catalog" / "videos.json")
        self.ledger = BudgetLedger(settings.project_root / "catalog" / "usage.json")
        self.youtube = youtube or YouTubeClient(settings)

    def build(
        self,
        experiment_id: str,
        language: Language,
        *,
        regenerate_storyboard: bool = False,
        rerender: bool = False,
    ) -> BuildOutcome:
        if regenerate_storyboard and rerender:
            raise ValueError("Choose either storyboard regeneration or local rerendering")
        experiments = self.source.experiments()
        try:
            experiment = experiments[experiment_id]
        except KeyError as exc:
            raise SourceError(f"Unknown experiment ID: {experiment_id}") from exc
        paths = bundle_paths(
            self.settings.project_root,
            experiment.id,
            language,
            experiment.source_hash,
        )
        existing = self.catalog.find(experiment.id, language, experiment.source_hash)
        if existing and existing.status is VideoStatus.FAILED and not regenerate_storyboard:
            raise ExternalServiceError("Storyboard is rejected; explicit regeneration required")
        storyboard = self._storyboard(
            experiment,
            language,
            paths,
            regenerate=regenerate_storyboard,
        )
        validate_science_review(storyboard, self.settings)
        fingerprint = build_fingerprint(storyboard, self.settings)
        paths = bundle_paths(
            self.settings.project_root, experiment.id, language, experiment.source_hash, fingerprint
        )
        if (
            existing
            and existing.build_hash == fingerprint
            and not regenerate_storyboard
            and (existing.youtube_id or (paths.video.exists() and not rerender))
        ):
            return BuildOutcome(record=existing, paths=paths, reused=True)
        save_storyboard(storyboard, paths.storyboard)
        record = VideoRecord(
            experiment_id=experiment.id,
            language=language,
            source_hash=experiment.source_hash,
            build_hash=fingerprint,
            template_version=storyboard.template_version,
            status=VideoStatus.STORYBOARDED,
            storyboard_path=str(paths.storyboard.relative_to(self.settings.project_root)),
            warnings=list(storyboard.review.warnings),
        )
        self.catalog.upsert(record)
        if not storyboard.review.approved:
            self.catalog.transition(
                experiment.id,
                language,
                experiment.source_hash,
                VideoStatus.FAILED,
            )
            raise ExternalServiceError(
                "Independent storyboard review rejected the draft; no TTS or render was started"
            )
        if storyboard.estimated_duration_seconds > float(
            self.settings.section("content")["hard_max_seconds"]
        ):
            raise ValueError("Storyboard exceeds the hard five-minute limit")

        narration = GoogleNarrator(self.settings, self.ledger).synthesize(
            storyboard, paths.narration, cache_only=rerender
        )
        save_segment_srt(narration.segments, paths.captions)
        renderer = PaperCutRenderer(self.settings)
        renderer.render_video(
            storyboard,
            narration.scene_durations,
            paths.silent_video,
            audio_path=paths.narration,
            segments=narration.segments,
        )
        renderer.render_thumbnail(storyboard, paths.thumbnail)
        mux_and_normalize(paths.silent_video, paths.narration, paths.video)
        validation = validate_media(paths.video, self.settings)
        write_checksums(
            [paths.storyboard, paths.captions, paths.thumbnail, paths.video],
            paths.checksum,
        )
        record = record.model_copy(
            update={
                "status": VideoStatus.RENDERED,
                "video_sha256": sha256_file(paths.video),
                "duration_seconds": validation.probe.duration_seconds,
                "warnings": [*record.warnings, *validation.warnings],
            }
        )
        self.catalog.upsert(record)
        return BuildOutcome(record=record, paths=paths, reused=False)

    def upload(
        self,
        experiment_id: str,
        language: Language,
        *,
        regenerate_storyboard: bool = False,
        rerender: bool = False,
    ) -> BuildOutcome:
        outcome = self.build(
            experiment_id,
            language,
            regenerate_storyboard=regenerate_storyboard,
            rerender=rerender,
        )
        record, paths = outcome.record, outcome.paths
        if record.status in {VideoStatus.PRIVATE, VideoStatus.UNLISTED, VideoStatus.PUBLIC}:
            return BuildOutcome(record=record, paths=paths, reused=True)
        if record.status is not VideoStatus.RENDERED or not paths.video.exists():
            raise ValueError("A validated rendered video is required before upload")
        require_asset_approval(self.settings, record.build_hash or "")
        storyboard = load_storyboard(paths.storyboard)
        upload = self.youtube.upload_private(
            storyboard,
            paths.video,
            paths.captions,
            paths.thumbnail,
        )
        record = self.catalog.transition(
            record.experiment_id,
            record.language,
            record.source_hash,
            VideoStatus.PRIVATE,
            youtube_id=upload.youtube_id,
        )
        return BuildOutcome(record=record, paths=paths, reused=upload.recovered)

    def release(self, scheduled_date: date, experiment_id: str) -> ReleaseOutcome:
        language = self.settings.language_for_date(scheduled_date)
        experiments = self.source.experiments()
        try:
            experiment = experiments[experiment_id]
        except KeyError as exc:
            raise SourceError(f"Unknown experiment ID: {experiment_id}") from exc
        expected_key = video_key(experiment.id, language, experiment.source_hash)
        recorded_release = self.catalog.release_for(scheduled_date)
        if (
            recorded_release
            and video_key(
                recorded_release.experiment_id,
                recorded_release.language,
                recorded_release.source_hash,
            )
            != expected_key
        ):
            return ReleaseOutcome(
                action="withheld",
                language=language,
                youtube_id=recorded_release.youtube_id,
                detail="This date is already bound to a different published video",
            )
        record = self.catalog.find(experiment.id, language, experiment.source_hash)
        if record is not None and record.status is VideoStatus.FAILED:
            return ReleaseOutcome(
                action="withheld",
                language=language,
                youtube_id=record.youtube_id,
                detail="Storyboard review failed; explicit regeneration is required",
            )
        if record is None or record.status in {
            VideoStatus.STORYBOARDED,
            VideoStatus.RENDERED,
        }:
            uploaded = self.upload(experiment_id, language)
            return ReleaseOutcome(
                action="private-draft",
                language=language,
                youtube_id=uploaded.record.youtube_id,
                detail="Current version was missing; it was left private for human review",
            )
        if recorded_release and recorded_release.build_hash != record.build_hash:
            return ReleaseOutcome(
                "withheld",
                language,
                recorded_release.youtube_id,
                "This date is bound to a different build",
            )
        if record.build_hash:
            paths = bundle_paths(
                self.settings.project_root, experiment.id, language, experiment.source_hash
            )
            current_storyboard = load_storyboard(paths.storyboard)
            if build_fingerprint(current_storyboard, self.settings) != record.build_hash:
                return ReleaseOutcome(
                    "withheld",
                    language,
                    record.youtube_id,
                    "Current content differs from approved build",
                )
            require_asset_approval(self.settings, record.build_hash)
        if record.youtube_id is None:
            raise ValueError("Catalog record has no YouTube ID")
        if record.status is VideoStatus.PUBLIC:
            self._record_release(scheduled_date, record)
            return ReleaseOutcome(
                action="no-op",
                language=language,
                youtube_id=record.youtube_id,
                detail="Current language/source version is already public",
            )
        remote_status = self.youtube.privacy_status(record.youtube_id)
        if remote_status == "public":
            if record.status is not VideoStatus.UNLISTED:
                raise ExternalServiceError(
                    "YouTube is public without a recorded unlisted approval transition"
                )
            self.catalog.transition(
                experiment.id,
                language,
                experiment.source_hash,
                VideoStatus.PUBLIC,
            )
            self._record_release(scheduled_date, record)
            return ReleaseOutcome(
                action="no-op",
                language=language,
                youtube_id=record.youtube_id,
                detail="YouTube already reports this version as public",
            )
        if remote_status != "unlisted":
            self.catalog.transition(
                experiment.id,
                language,
                experiment.source_hash,
                VideoStatus.PRIVATE,
            )
            return ReleaseOutcome(
                action="withheld",
                language=language,
                youtube_id=record.youtube_id,
                detail="Video is still private; nothing unreviewed was published",
            )
        self.catalog.transition(
            experiment.id,
            language,
            experiment.source_hash,
            VideoStatus.UNLISTED,
        )
        self.youtube.make_public(record.youtube_id)
        self.catalog.transition(
            experiment.id,
            language,
            experiment.source_hash,
            VideoStatus.PUBLIC,
        )
        self._record_release(scheduled_date, record)
        return ReleaseOutcome(
            action="published",
            language=language,
            youtube_id=record.youtube_id,
            detail="Approved current version was made public",
        )

    def _record_release(self, scheduled_date: date, record: VideoRecord) -> None:
        if record.youtube_id is None:
            raise ValueError("Cannot record a release without a YouTube ID")
        self.catalog.record_release(
            ReleaseRecord(
                date=scheduled_date,
                experiment_id=record.experiment_id,
                language=record.language,
                source_hash=record.source_hash,
                youtube_id=record.youtube_id,
                build_hash=record.build_hash,
            )
        )

    def _storyboard(
        self,
        experiment: ExperimentSnapshot,
        language: Language,
        paths: BundlePaths,
        *,
        regenerate: bool,
    ) -> Storyboard:
        if paths.storyboard.exists() and not regenerate:
            storyboard = load_storyboard(paths.storyboard)
            expected = (experiment.id, experiment.source_hash, language)
            actual = (
                storyboard.experiment_id,
                storyboard.source_hash,
                storyboard.language,
            )
            if actual != expected:
                raise ValueError("Saved storyboard identity does not match the source")
            return storyboard
        generator = StoryboardGenerator(self.settings, self.ledger)
        attempts = int(self.settings.section("budgets")["max_generation_attempts"])
        storyboard: Storyboard | None = None
        last_error: ExternalServiceError | None = None
        for _ in range(attempts):
            try:
                storyboard = generator.generate(experiment, language)
            except ExternalServiceError as exc:
                last_error = exc
                continue
            save_storyboard(storyboard, paths.storyboard)
            if storyboard.review.approved:
                break
        if storyboard is None:
            assert last_error is not None
            raise last_error
        assert storyboard is not None
        return storyboard
