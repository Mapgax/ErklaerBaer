from datetime import date

import pytest

from erklaerbaer.errors import ExternalServiceError
from erklaerbaer.models import Language, ReleaseRecord, VideoRecord, VideoStatus
from erklaerbaer.pipeline import VideoPipeline

from .factories import make_settings, sample_experiment


class StaticSource:
    def __init__(self, experiment):
        self.experiment = experiment

    def experiments(self):
        return {self.experiment.id: self.experiment}


class FakeYouTube:
    def __init__(self, status: str):
        self.status = status
        self.public_calls: list[str] = []
        self.status_calls: list[str] = []

    def privacy_status(self, youtube_id: str) -> str:
        self.status_calls.append(youtube_id)
        return self.status

    def make_public(self, youtube_id: str) -> None:
        self.public_calls.append(youtube_id)


def _record(pipeline, status, language=Language.GERMAN, source_hash=None):
    experiment = pipeline.source.experiment
    record = VideoRecord(
        experiment_id=experiment.id,
        language=language,
        source_hash=source_hash or experiment.source_hash,
        template_version="1",
        status=status,
        youtube_id="video-123",
        storyboard_path="storyboards/example.json",
    )
    pipeline.catalog.upsert(record)
    return record


def test_private_video_is_withheld(tmp_path):
    settings = make_settings(tmp_path)
    youtube = FakeYouTube("private")
    pipeline = VideoPipeline(settings, source=StaticSource(sample_experiment()), youtube=youtube)
    _record(pipeline, VideoStatus.PRIVATE)
    outcome = pipeline.release(date(2026, 9, 4), "blasen-test")
    assert outcome.action == "withheld"
    assert youtube.public_calls == []


def test_unlisted_approval_is_required_then_published(tmp_path, monkeypatch):
    settings = make_settings(tmp_path)
    youtube = FakeYouTube("unlisted")
    pipeline = VideoPipeline(settings, source=StaticSource(sample_experiment()), youtube=youtube)
    _record(pipeline, VideoStatus.PRIVATE)
    monkeypatch.setenv("YOUTUBE_API_AUDIT_COMPLETE", "true")
    monkeypatch.setenv("DRY_RUN", "false")
    outcome = pipeline.release(date(2026, 9, 4), "blasen-test")
    assert outcome.action == "published"
    assert youtube.public_calls == ["video-123"]
    record = pipeline.catalog.find("blasen-test", Language.GERMAN, sample_experiment().source_hash)
    assert record is not None and record.status is VideoStatus.PUBLIC


def test_unexpected_private_to_public_remote_state_fails_closed(tmp_path):
    settings = make_settings(tmp_path)
    youtube = FakeYouTube("public")
    pipeline = VideoPipeline(settings, source=StaticSource(sample_experiment()), youtube=youtube)
    _record(pipeline, VideoStatus.PRIVATE)
    with pytest.raises(ExternalServiceError, match="without a recorded unlisted"):
        pipeline.release(date(2026, 9, 4), "blasen-test")


def test_opposite_language_record_is_never_substituted(tmp_path, monkeypatch):
    settings = make_settings(tmp_path)
    youtube = FakeYouTube("public")
    pipeline = VideoPipeline(settings, source=StaticSource(sample_experiment()), youtube=youtube)
    _record(pipeline, VideoStatus.PUBLIC, language=Language.DUTCH)

    def fake_upload(experiment_id, language):
        assert language is Language.GERMAN
        raise RuntimeError("required language build attempted")

    monkeypatch.setattr(pipeline, "upload", fake_upload)
    with pytest.raises(RuntimeError, match="required language"):
        pipeline.release(date(2026, 9, 4), "blasen-test")


def test_stale_source_hash_is_never_published(tmp_path, monkeypatch):
    settings = make_settings(tmp_path)
    experiment = sample_experiment()
    pipeline = VideoPipeline(
        settings, source=StaticSource(experiment), youtube=FakeYouTube("unlisted")
    )
    _record(pipeline, VideoStatus.UNLISTED, source_hash="0" * 16)

    def fake_upload(experiment_id, language):
        raise RuntimeError("current source build attempted")

    monkeypatch.setattr(pipeline, "upload", fake_upload)
    with pytest.raises(RuntimeError, match="current source"):
        pipeline.release(date(2026, 9, 4), experiment.id)


def test_second_experiment_cannot_publish_on_same_date(tmp_path):
    settings = make_settings(tmp_path)
    experiment = sample_experiment()
    youtube = FakeYouTube("unlisted")
    pipeline = VideoPipeline(settings, source=StaticSource(experiment), youtube=youtube)
    pipeline.catalog.record_release(
        ReleaseRecord(
            date=date(2026, 9, 4),
            experiment_id="different-test",
            language=Language.GERMAN,
            source_hash="1" * 16,
            youtube_id="earlier-video",
        )
    )
    outcome = pipeline.release(date(2026, 9, 4), experiment.id)
    assert outcome.action == "withheld"
    assert outcome.youtube_id == "earlier-video"
    assert youtube.public_calls == []


def test_duplicate_dispatch_for_public_version_is_no_op(tmp_path):
    settings = make_settings(tmp_path)
    youtube = FakeYouTube("private")
    pipeline = VideoPipeline(settings, source=StaticSource(sample_experiment()), youtube=youtube)
    _record(pipeline, VideoStatus.PUBLIC)
    first = pipeline.release(date(2026, 9, 4), "blasen-test")
    second = pipeline.release(date(2026, 9, 4), "blasen-test")
    assert first.action == second.action == "no-op"
    assert youtube.status_calls == []
    assert youtube.public_calls == []


def test_rejected_storyboard_is_not_retried_by_daily_release(tmp_path):
    settings = make_settings(tmp_path)
    youtube = FakeYouTube("unlisted")
    pipeline = VideoPipeline(settings, source=StaticSource(sample_experiment()), youtube=youtube)
    _record(pipeline, VideoStatus.FAILED)
    outcome = pipeline.release(date(2026, 9, 4), "blasen-test")
    assert outcome.action == "withheld"
    assert "explicit regeneration" in outcome.detail
    assert youtube.status_calls == []
