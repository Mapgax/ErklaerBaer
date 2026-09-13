"""A production slot picks a topic nobody has produced, and always the same one for its date."""

from datetime import date

import pytest

from erklaerbaer.config import ConfigurationError, load_settings
from erklaerbaer.models import ExperimentSnapshot, Language
from erklaerbaer.topics import candidates, slot_language, used_topics


def snapshot(topic):
    return ExperimentSnapshot(
        id=topic,
        title=topic,
        category="technik",
        fact="Ein Fakt, lang genug.",
        observed_result="Es passiert etwas.",
        explanation="Weil es so ist, genau.",
    )


def test_every_storyboarded_topic_counts_as_used(tmp_path):
    (tmp_path / "storyboards/v3/fall-wettrennen").mkdir(parents=True)
    (tmp_path / "storyboards/krabbeltier-safari").mkdir(parents=True)
    assert used_topics(tmp_path) == {"fall-wettrennen", "krabbeltier-safari"}


def test_candidates_skip_used_topics_and_are_stable_for_a_date():
    experiments = {t: snapshot(t) for t in ("a", "b", "c", "d", "e")}
    first = candidates(experiments, {"c"}, date(2026, 9, 14))
    assert "c" not in [s.id for s in first]
    assert [s.id for s in first] == [
        s.id for s in candidates(experiments, {"c"}, date(2026, 9, 14))
    ]
    assert sorted(s.id for s in first) == ["a", "b", "d", "e"]


def test_monday_is_german_thursday_is_dutch_and_other_days_have_no_slot():
    settings = load_settings()
    assert slot_language(settings, date(2026, 9, 14)) is Language.GERMAN
    assert slot_language(settings, date(2026, 9, 17)) is Language.DUTCH
    with pytest.raises(ConfigurationError):
        slot_language(settings, date(2026, 9, 15))
