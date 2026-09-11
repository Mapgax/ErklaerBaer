import pytest
from pydantic import ValidationError

from erklaerbaer.audio import _speech_markup
from erklaerbaer.captions import render_srt
from erklaerbaer.models import Scene, ScenePrimitive, Storyboard

from .factories import sample_storyboard


def test_scene_rejects_more_than_five_visible_words():
    with pytest.raises(ValidationError, match="at most five words"):
        Scene(
            scene_id="too-many",
            primitive=ScenePrimitive.QUESTION,
            narration="This narration is long enough for model validation.",
            on_screen_words=["one two three", "four five six"],
            visual_tokens=["bubble"],
            claim_anchors=["fact"],
        )


def test_srt_has_matching_language_text_and_monotone_timing():
    storyboard = sample_storyboard()
    result = render_srt(storyboard, [15.0] * len(storyboard.scenes))
    assert storyboard.scenes[0].narration.split()[0] in result
    assert "00:00:00,000 -->" in result
    assert "00:02:00,000" in result


def test_storyboard_rejects_sparse_narration_for_its_runtime():
    payload = sample_storyboard().model_dump(mode="json")
    payload["scenes"] = [
        {**scene, "narration": "This sentence is intentionally far too short."}
        for scene in payload["scenes"]
    ]
    with pytest.raises(ValidationError, match="narration pace"):
        Storyboard.model_validate(payload)


def test_storyboard_rejects_duration_that_does_not_match_scene_hints():
    payload = sample_storyboard().model_dump(mode="json")
    payload["estimated_duration_seconds"] = 150
    with pytest.raises(ValidationError, match="sum of scene duration hints"):
        Storyboard.model_validate(payload)


def test_prediction_tts_has_a_thinking_pause_before_the_answer():
    scene = (
        sample_storyboard()
        .scenes[-2]
        .model_copy(update={"narration": "Welke heeft veertien poten? Dat is de pissebed."})
    )
    markup = _speech_markup(scene)
    assert "poten? [pause long] Dat" in markup
