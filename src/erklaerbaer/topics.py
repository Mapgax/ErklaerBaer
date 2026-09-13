"""Pick the next never-used MINT topic for a production slot.

A topic counts as used once any storyboard exists for it, in any language or version, so the
tracked storyboards/ tree is the single record and nothing can be produced twice.
"""

from __future__ import annotations

import random
from datetime import date
from pathlib import Path

from .config import ConfigurationError, Settings
from .models import ExperimentSnapshot, Language

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def used_topics(root: Path) -> set[str]:
    boards = root / "storyboards"
    top = {p.name for p in boards.iterdir() if p.is_dir() and p.name != "v3"}
    return top | {p.name for p in (boards / "v3").iterdir() if p.is_dir()}


def slot_language(settings: Settings, day: date) -> Language:
    """The language a production slot on this day is for; any other day has no slot."""
    for slot in settings.section("production_v3")["slots"]:
        if slot["weekday"] == WEEKDAYS[day.weekday()]:
            return Language(slot["language"])
    raise ConfigurationError(f"{day.isoformat()} ({WEEKDAYS[day.weekday()]}) is not a slot")


def candidates(
    experiments: dict[str, ExperimentSnapshot], used: set[str], day: date
) -> list[ExperimentSnapshot]:
    """Every unused topic in an order fixed by the date, so a retried slot sees the same list."""
    fresh = sorted(topic for topic in experiments if topic not in used)
    random.Random(day.isoformat()).shuffle(fresh)
    return [experiments[topic] for topic in fresh]
