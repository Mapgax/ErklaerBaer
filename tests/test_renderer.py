from pathlib import Path

import numpy as np
from PIL import Image

from erklaerbaer.renderer import PaperCutRenderer, _fade_through_blank, _leg_pair_count
from erklaerbaer.visuals import canonical_visual_token

from .factories import make_settings, sample_storyboard


def test_every_scene_primitive_matches_golden_snapshot(tmp_path):
    settings = make_settings(tmp_path)
    storyboard = sample_storyboard()
    renderer = PaperCutRenderer(settings, width=480, height=270, fps=5)
    golden_root = Path(__file__).parent / "golden"
    for scene in storyboard.scenes:
        frame = renderer.render_frame(storyboard, scene, progress=0.55, mouth=0.3)
        expected = Image.open(golden_root / f"{scene.primitive.value}.png").convert("RGB")
        actual = np.asarray(frame, dtype=np.int16)
        reference = np.asarray(expected, dtype=np.int16)
        assert actual.shape == reference.shape
        assert float(np.mean(np.abs(actual - reference))) < 8.0


def test_long_dutch_label_stays_inside_canvas(tmp_path):
    settings = make_settings(tmp_path)
    storyboard = sample_storyboard()
    scene = storyboard.scenes[0].model_copy(
        update={"on_screen_words": ["Opwaartse kracht ontdekken"]}
    )
    renderer = PaperCutRenderer(settings, width=480, height=270, fps=5)
    frame = renderer.render_frame(storyboard, scene, progress=0.5)
    assert frame.size == (480, 270)
    assert frame.getbbox() == (0, 0, 480, 270)


def test_thumbnail_meets_youtube_dimensions_and_size(tmp_path):
    settings = make_settings(tmp_path)
    storyboard = sample_storyboard()
    renderer = PaperCutRenderer(settings, width=480, height=270, fps=5)
    output = tmp_path / "thumbnail.jpg"
    renderer.render_thumbnail(storyboard, output)
    with Image.open(output) as thumbnail:
        assert thumbnail.size == (1280, 720)
    assert output.stat().st_size < 2_000_000


def test_scene_transition_passes_through_text_free_frame():
    prior = Image.new("RGB", (4, 4), (200, 0, 0))
    current = Image.new("RGB", (4, 4), (0, 0, 200))
    blank = Image.new("RGB", (4, 4), (248, 239, 216))
    midpoint = _fade_through_blank(prior, current, blank, 0.5)
    assert np.array_equal(np.asarray(midpoint), np.asarray(blank))


def test_animal_anatomy_uses_exact_leg_pair_counts():
    assert _leg_pair_count("insect") == 3
    assert _leg_pair_count("spider") == 4
    assert _leg_pair_count("woodlouse") == 7


def test_abstract_cycle_placeholder_is_not_a_visual_token():
    assert canonical_visual_token("cycle_complete") is None
