"""Geometry and timing the falling template can reason about, asserted rather than eyeballed."""

import json
from pathlib import Path

import pytest

from erklaerbaer import collage_fall as fall
from erklaerbaer.models import Storyboard

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "storyboards/v3/fall-wettrennen/nl-NL/c120949aca72eba7.json"


def test_one_fall_law_lands_everything_in_order():
    assert fall.stone_height(0) == fall.DROP
    assert fall.stone_height(fall.FALL_SECONDS) == pytest.approx(0, abs=1e-6)
    assert fall.ball_height(fall.FALL_SECONDS) > 0
    assert fall.ball_height(fall.FALL_SECONDS * fall.BALL_LAG) == pytest.approx(0, abs=1e-6)
    assert fall.paper_height(fall.FALL_SECONDS) > fall.DROP * 0.6
    assert fall.paper_height(fall.PAPER_SECONDS + 0.01) == 0


def test_strobe_gaps_grow_at_equal_time_steps():
    steps = [fall.stone_height(k * fall.FALL_SECONDS / 5) for k in range(6)]
    gaps = [a - b for a, b in zip(steps, steps[1:], strict=False)]
    assert all(later > earlier for earlier, later in zip(gaps, gaps[1:], strict=False))


def test_objects_sit_on_the_flap_and_the_hanging_flap_clears_the_floor():
    flap_right = fall.POST_X - fall.POST_WIDTH / 2
    assert fall.LANE_STONE - fall.STONE[0] / 2 > fall.FLAP_LEFT
    sheet_reach = fall.SHEET[0] / 2 + fall.SHEET[1] / 2 * fall.SHEET_SKEW
    assert fall.LANE_OTHER + sheet_reach < flap_right
    assert flap_right - fall.FLAP_LEFT < fall.DROP


def test_air_field_never_reaches_the_hanging_flap():
    flap_face = fall.POST_X - fall.POST_WIDTH / 2 - fall.FLAP_THICKNESS
    widest = max(x + fall.AIR_PUSH for x, _ in fall.air_lattice())
    assert widest + fall.AIR_RADIUS < flap_face


@pytest.mark.parametrize("framing", ["establish", "drop", "strobe", "air", "crumple"])
def test_resting_props_stay_below_the_heading(framing):
    board = Storyboard.model_validate_json(BOARD.read_text())
    scene = next(s for s in board.scenes if s.shot.framing == framing)
    view = fall.view_for(scene)
    top = view.y(fall.DROP + fall.STONE[1])
    assert top > fall.HEADING_FLOOR


def test_the_pilot_uses_all_six_bear_actions():
    board = json.loads(BOARD.read_text())
    used = {s["mascot"]["action"] for s in board["scenes"] if s["mascot"]["visible"]}
    assert used == {"neutral", "lift", "explain", "think", "surprise", "aha"}


def test_authored_pauses_hold_the_landing_and_the_crumple_in_silence():
    knock_ends = fall.RELEASE_DELAY + fall.FALL_SECONDS * fall.BALL_LAG + fall.KNOCK_SECONDS
    assert knock_ends + 0.05 < fall.RELEASE_PAUSE
    assert fall.CRUMPLE_DELAY + fall.CRUMPLE_SECONDS + 0.05 < fall.CRUMPLE_PAUSE


def test_pushed_air_marks_never_touch_their_neighbours():
    assert fall.AIR_PUSH < fall.AIR_SPACING - 2 * fall.AIR_RADIUS


def test_rig_floor_is_where_the_bear_stands():
    board = Storyboard.model_validate_json(BOARD.read_text())
    for scene in board.scenes:
        if scene.mascot.visible and scene.shot.framing != "predict":
            assert fall.view_for(scene).floor_y == fall.scene_bear_box(scene)[3]


def test_a_missing_beat_names_the_scene_instead_of_stopiteration():
    board = Storyboard.model_validate_json(BOARD.read_text())
    weigh = next(s for s in board.scenes if s.shot.framing == "weigh")
    with pytest.raises(ValueError, match="release"):
        fall.release_time(weigh, [])
