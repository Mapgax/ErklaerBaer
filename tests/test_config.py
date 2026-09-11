from datetime import date, timedelta

from erklaerbaer.models import Language

from .factories import make_settings


def test_documented_parity_examples(tmp_path):
    settings = make_settings(tmp_path)
    assert settings.language_for_date(date(2026, 9, 4)) is Language.GERMAN
    assert settings.language_for_date(date(2026, 9, 5)) is Language.DUTCH


def test_parity_continues_across_boundaries_and_leap_day(tmp_path):
    settings = make_settings(tmp_path)
    dates = [
        date(2023, 12, 31),
        date(2024, 1, 1),
        date(2024, 2, 28),
        date(2024, 2, 29),
        date(2024, 3, 1),
    ]
    for left, right in zip(dates, dates[1:], strict=False):
        if right - left == timedelta(days=1):
            assert settings.language_for_date(left) is not settings.language_for_date(right)
    for current in dates:
        ordinal = (current - date(1970, 1, 1)).days
        expected = Language.GERMAN if ordinal % 2 == 0 else Language.DUTCH
        assert settings.language_for_date(current) is expected
