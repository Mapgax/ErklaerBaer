import hashlib
import io
import json
import wave
from types import SimpleNamespace

import pytest
from PIL import Image

from erklaerbaer.audio import GoogleNarrator
from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.build_identity import (
    build_fingerprint,
    content_only,
    require_asset_approval,
)
from erklaerbaer.errors import BudgetExceeded, ExternalServiceError
from erklaerbaer.mascot_library import MascotLibrary
from erklaerbaer.mechanisms import beat_at
from erklaerbaer.science_review import validate_science_review
from erklaerbaer.speech_cache import digest_json
from erklaerbaer.storyboards import load_storyboard

from .factories import make_settings, sample_storyboard


def test_task_allowance_does_not_renew_or_erase_months(tmp_path, monkeypatch):
    ledger = BudgetLedger(tmp_path / "usage.json")
    ledger.reserve("bfl_credits_reserved", 100, 100, dry_run=False)
    ledger.initialize_production_task()
    ledger.reserve("bfl_credits_reserved", 20, 400, dry_run=False)
    ledger.initialize_production_task()
    assert ledger.current("bfl_credits_reserved") == 120
    monkeypatch.setattr(ledger, "_month_key", lambda: "2099-01")
    ledger.reserve("bfl_credits_reserved", 280, 400, dry_run=False)
    with pytest.raises(BudgetExceeded):
        ledger.reserve("bfl_credits_reserved", 20, 400, dry_run=False)
    assert ledger.load()["production_v2"]["used"]["bfl_credits_reserved"] == 300


def test_visual_rerender_reuses_audio_and_caption_intervals(tmp_path, monkeypatch):
    from google.cloud import texttospeech

    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "fake")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake.json")
    calls = []

    def synthesize(**kwargs):
        calls.append(kwargs)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
            wav.writeframes(b"\x10\x00" * 48000)
        return SimpleNamespace(audio_content=buffer.getvalue())

    monkeypatch.setattr(
        texttospeech, "TextToSpeechClient", lambda: SimpleNamespace(synthesize_speech=synthesize)
    )
    ledger = BudgetLedger(tmp_path / "usage.json")
    narrator = GoogleNarrator(make_settings(tmp_path), ledger)
    storyboard = sample_storyboard()
    first = narrator.synthesize(storyboard, tmp_path / "first.wav")
    usage = ledger.load()
    storyboard.scenes[0].on_screen_words = ["Changed visual"]
    monkeypatch.setattr(
        texttospeech,
        "TextToSpeechClient",
        lambda: pytest.fail("Visual rerender contacted provider"),
    )
    second = narrator.synthesize(storyboard, tmp_path / "second.wav", cache_only=True)
    assert (tmp_path / "first.wav").read_bytes() == (tmp_path / "second.wav").read_bytes()
    assert second.character_count == 0
    assert ledger.load() == usage
    assert first.segments == second.segments
    assert second.segments[0]["end"] < second.segments[1]["start"]
    storyboard.scenes[0].narration += " Changed speech."
    with pytest.raises(ExternalServiceError, match="not cached"):
        narrator.synthesize(storyboard, tmp_path / "third.wav", cache_only=True)


def test_uncertain_tts_is_not_submitted_twice(tmp_path, monkeypatch):
    from google.cloud import texttospeech

    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "fake")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake.json")
    calls = []

    def fail(**kwargs):
        calls.append(1)
        raise TimeoutError()

    monkeypatch.setattr(
        texttospeech, "TextToSpeechClient", lambda: SimpleNamespace(synthesize_speech=fail)
    )
    narrator = GoogleNarrator(make_settings(tmp_path), BudgetLedger(tmp_path / "usage.json"))
    with pytest.raises(ExternalServiceError, match="TimeoutError"):
        narrator.synthesize(sample_storyboard(), tmp_path / "first.wav")
    with pytest.raises(ExternalServiceError, match="Uncertain"):
        narrator.synthesize(sample_storyboard(), tmp_path / "first.wav")
    assert len(calls) == 1


def test_mascot_loop_wraps_and_one_shot_holds(tmp_path):
    actions = {}
    for action in ("neutral", "lift", "explain", "think", "surprise", "aha"):
        frames = []
        for index in range(3):
            path = tmp_path / action / f"{index:04}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGBA", (6, 8), (index, 0, 0, 255)).save(path)
            frames.append({"file": str(path.relative_to(tmp_path)), "sha256": "unused"})
        actions[action] = {"loop": action == "neutral", "frames": frames}
    (tmp_path / "manifest.json").write_text(json.dumps({"fps": 30, "actions": actions}))
    library = MascotLibrary(tmp_path)
    assert library.frame_index("neutral", 4 / 30) == 1
    assert library.frame_index("surprise", 4 / 30) == 2


def test_mechanism_uses_measured_segment_start():
    root = __import__("pathlib").Path(__file__).parents[1]
    board = load_storyboard(root / "storyboards/springende-muenze/de-DE/0d6d2f1d3eb3b75d.json")
    scene = board.scenes[0]
    timings = [
        {"scene_id": scene.scene_id, "segment_id": segment.segment_id, "scene_start": index * 2}
        for index, segment in enumerate(scene.segments)
    ]
    assert beat_at(scene, 0.5, timings).action == "observe"
    assert beat_at(scene, 2.1, timings).action == "heat"
    assert beat_at(scene, 4.1, timings).action == "lift"


def test_review_status_does_not_change_build_identity(tmp_path):
    settings = make_settings(tmp_path)
    storyboard = sample_storyboard()
    first = build_fingerprint(storyboard, settings)
    changed = storyboard.model_copy(
        update={"review": storyboard.review.model_copy(update={"approved": False})}
    )
    assert build_fingerprint(changed, settings) == first


def test_stale_science_review_is_rejected(tmp_path):
    root = __import__("pathlib").Path(__file__).parents[1]
    board = load_storyboard(root / "storyboards/springende-muenze/de-DE/0d6d2f1d3eb3b75d.json")
    settings = make_settings(tmp_path)
    evidence = tmp_path / "docs/evidence"
    evidence.mkdir(parents=True)
    source = root / "docs/evidence/springende-muenze.json"
    (evidence / source.name).write_bytes(source.read_bytes())
    (evidence / "springende-muenze.review.json").write_text(
        json.dumps({"content_hash": "stale", "result": {"approved": True, "warnings": []}})
    )
    with pytest.raises(ValueError, match="stale"):
        validate_science_review(board, settings)


def _write_test_library(root, value: bytes = b"first"):
    library = root / "assets/mascot/rig/v2"
    frame = library / "frames/neutral/0000.png"
    frame.parent.mkdir(parents=True, exist_ok=True)
    frame.write_bytes(value)
    checksum = hashlib.sha256(value).hexdigest()
    actions = {
        action: {
            "loop": action == "neutral",
            "frames": [{"file": str(frame.relative_to(library)), "sha256": checksum}],
        }
        for action in ("neutral", "lift", "explain", "think", "surprise", "aha")
    }
    manifest = {
        "schema_version": 2,
        "review_status": "provisional",
        "owner_approved": False,
        "actions": actions,
    }
    (library / "manifest.json").write_text(json.dumps(manifest))
    return manifest


def test_mascot_bytes_invalidate_build_fingerprint(tmp_path):
    settings = make_settings(tmp_path)
    storyboard = sample_storyboard()
    _write_test_library(tmp_path)
    first = build_fingerprint(storyboard, settings)
    _write_test_library(tmp_path, b"changed")
    assert build_fingerprint(storyboard, settings) != first


def test_review_bookkeeping_does_not_invalidate_exact_asset_approval(tmp_path):
    settings = make_settings(tmp_path)
    manifest = _write_test_library(tmp_path)
    build_hash = "a" * 24
    approvals = tmp_path / "catalog/creative-approvals.json"
    approvals.parent.mkdir(parents=True)
    approvals.write_text(
        json.dumps(
            {
                "builds": [build_hash],
                "mascots": [digest_json(content_only(manifest))],
            }
        )
    )
    manifest["review_status"] = "owner-approved"
    manifest["owner_approved"] = True
    path = tmp_path / "assets/mascot/rig/v2/manifest.json"
    path.write_text(json.dumps(manifest))
    require_asset_approval(settings, build_hash)
