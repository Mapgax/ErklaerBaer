from types import SimpleNamespace

import pytest

from erklaerbaer.audio import GoogleNarrator
from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.errors import ExternalServiceError
from erklaerbaer.models import Language, ReviewResult
from erklaerbaer.storyboards import (
    StoryboardGenerator,
    _bare_localized_title,
    _enforce_blocking_warning_policy,
    _normalized_writer_payload,
    _response_json_payload,
)
from erklaerbaer.youtube import YouTubeClient, content_marker

from .factories import make_settings, sample_experiment, sample_storyboard


def _enable_live_mode(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "false")


def test_storyboard_timeout_is_normalized_and_budgeted(tmp_path, monkeypatch):
    import anthropic

    class FailingMessages:
        def create(self, **kwargs):
            raise TimeoutError("provider details must not cross the boundary")

    _enable_live_mode(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "placeholder")
    monkeypatch.setattr(
        anthropic,
        "Anthropic",
        lambda **kwargs: SimpleNamespace(messages=FailingMessages()),
    )
    settings = make_settings(tmp_path)
    ledger = BudgetLedger(tmp_path / "usage.json")
    with pytest.raises(ExternalServiceError, match="TimeoutError"):
        StoryboardGenerator(settings, ledger).generate(sample_experiment(), Language.GERMAN)
    assert ledger.current("llm_calls") == 1


def test_storyboard_schema_error_reports_only_locations_and_types(tmp_path, monkeypatch):
    import anthropic

    class InvalidMessages:
        def create(self, **kwargs):
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="text",
                        text='{"secret_provider_text": "must-not-appear"}',
                    )
                ]
            )

    _enable_live_mode(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "placeholder")
    monkeypatch.setattr(
        anthropic,
        "Anthropic",
        lambda **kwargs: SimpleNamespace(messages=InvalidMessages()),
    )
    settings = make_settings(tmp_path)
    ledger = BudgetLedger(tmp_path / "usage.json")
    with pytest.raises(ExternalServiceError) as caught:
        StoryboardGenerator(settings, ledger).generate(sample_experiment(), Language.GERMAN)
    message = str(caught.value)
    assert "did not match the schema" in message
    assert "secret_provider_text" not in message


def test_writer_shape_normalization_is_limited_to_ids_and_labels():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(
                type="text",
                text=(
                    '{"scenes": ['
                    '{"scene_id": "macro_to_micro", '
                    '"narration": "Science stays exactly as written.", '
                    '"on_screen_words": ["one two three", "four five six"], '
                    '"model_note": "drop me"}'
                    '], "word_count": 999}'
                ),
            )
        ]
    )
    payload = _normalized_writer_payload(response)
    assert payload["scenes"][0]["scene_id"] == "macro-to-micro"
    assert payload["scenes"][0]["on_screen_words"] == ["one two three", "four five"]
    assert payload["scenes"][0]["narration"] == "Science stays exactly as written."
    assert "model_note" not in payload["scenes"][0]
    assert "word_count" not in payload


def test_localized_title_wrapper_is_removed_before_template_application():
    assert (
        _bare_localized_title("NL | De Krabbeltier-Safari – simpel uitgelegd", Language.DUTCH)
        == "De Krabbeltier-Safari"
    )
    assert (
        _bare_localized_title("Die springende Münze – einfach erklärt", Language.GERMAN)
        == "Die springende Münze"
    )


def test_json_payload_allows_provider_wrapper_but_not_incomplete_json():
    wrapped = SimpleNamespace(
        content=[SimpleNamespace(type="text", text='Draft follows:\n{"approved": true}\nDone.')]
    )
    assert _response_json_payload(wrapped) == {"approved": True}

    incomplete = SimpleNamespace(content=[SimpleNamespace(type="text", text='{"approved":')])
    with pytest.raises(ValueError):
        _response_json_payload(incomplete)


def test_blocking_review_warning_overrides_model_approval():
    review = ReviewResult(
        approved=True,
        warnings=["One claim is borderline speculative and should be corrected."],
    )
    assert _enforce_blocking_warning_policy(review).approved is False


def test_minor_review_warning_remains_approved():
    review = ReviewResult(
        approved=True,
        warnings=["A shorter thumbnail label could be slightly clearer."],
    )
    assert _enforce_blocking_warning_policy(review).approved is True


def test_positive_supported_claim_warning_does_not_block():
    review = ReviewResult(
        approved=True,
        warnings=["All scientific claims are supported; no unsupported claims detected."],
    )
    assert _enforce_blocking_warning_policy(review).approved is True


def test_extrapolation_warning_blocks_approval():
    review = ReviewResult(
        approved=True,
        warnings=["The larger-container relationship is extrapolated beyond the source."],
    )
    assert _enforce_blocking_warning_policy(review).approved is False


def test_code_switching_warning_blocks_approval():
    review = ReviewResult(
        approved=True,
        warnings=["Scene 2 uses German 'Die' instead of Dutch 'De'."],
    )
    assert _enforce_blocking_warning_policy(review).approved is False


def test_tts_timeout_is_normalized_and_budgeted(tmp_path, monkeypatch):
    from google.cloud import texttospeech

    class FailingTTS:
        def synthesize_speech(self, **kwargs):
            raise TimeoutError("provider details must not cross the boundary")

    _enable_live_mode(monkeypatch)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "placeholder")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/private/placeholder.json")
    monkeypatch.setattr(texttospeech, "TextToSpeechClient", lambda: FailingTTS())
    settings = make_settings(tmp_path)
    ledger = BudgetLedger(tmp_path / "usage.json")
    storyboard = sample_storyboard()
    with pytest.raises(ExternalServiceError, match="TimeoutError"):
        GoogleNarrator(settings, ledger).synthesize(storyboard, tmp_path / "audio.wav")
    assert ledger.current("tts_characters") == len(storyboard.scenes[0].narration)


def test_expired_oauth_is_reported_without_token_details(tmp_path, monkeypatch):
    from google.oauth2 import credentials as credentials_module

    class ExpiredCredentials:
        def __init__(self, **kwargs):
            pass

        def refresh(self, request):
            raise RuntimeError("token-value-that-must-not-appear")

    _enable_live_mode(monkeypatch)
    monkeypatch.setenv("YOUTUBE_CLIENT_ID", "client")
    monkeypatch.setenv("YOUTUBE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("YOUTUBE_REFRESH_TOKEN", "refresh")
    monkeypatch.setattr(credentials_module, "Credentials", ExpiredCredentials)
    settings = make_settings(tmp_path)
    with pytest.raises(ExternalServiceError) as caught:
        _ = YouTubeClient(settings).service
    assert "token-value" not in str(caught.value)
    assert "RuntimeError" in str(caught.value)


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class RecoveryService:
    def __init__(self, marker):
        self.marker = marker

    def channels(self):
        return self

    def playlistItems(self):
        return self

    def videos(self):
        return self

    def list(self, **kwargs):
        part = kwargs["part"]
        if part == "id,snippet,contentDetails":
            return FakeRequest(
                {
                    "items": [
                        {
                            "id": "channel",
                            "contentDetails": {"relatedPlaylists": {"uploads": "uploads"}},
                        }
                    ]
                }
            )
        if part == "contentDetails":
            return FakeRequest({"items": [{"contentDetails": {"videoId": "recovered-id"}}]})
        if part == "snippet":
            return FakeRequest(
                {"items": [{"id": "recovered-id", "snippet": {"description": self.marker}}]}
            )
        raise AssertionError(kwargs)


def test_partial_upload_is_recovered_by_content_marker(tmp_path, monkeypatch):
    _enable_live_mode(monkeypatch)
    storyboard = sample_storyboard()
    service = RecoveryService(content_marker(storyboard))
    client = YouTubeClient(make_settings(tmp_path), service=service)
    completed: list[str] = []
    monkeypatch.setattr(
        client,
        "_ensure_post_upload_assets",
        lambda youtube_id, *args: completed.append(youtube_id),
    )
    result = client.upload_private(
        storyboard,
        tmp_path / "video.mp4",
        tmp_path / "captions.srt",
        tmp_path / "thumbnail.jpg",
    )
    assert result.recovered is True
    assert result.youtube_id == "recovered-id"
    assert completed == ["recovered-id"]
