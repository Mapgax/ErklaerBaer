import hashlib
import json
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.collage_guitar import (
    AIR,
    AIR_BOUNDS,
    AIR_SOURCE,
    air_displacement,
    air_lattice,
    air_onset,
    string_points,
)
from erklaerbaer.errors import BudgetExceeded, ExternalServiceError
from erklaerbaer.expressive_speech import reserve_request, speech_identity
from erklaerbaer.models import SpeechSegment
from erklaerbaer.weekly_queue import WeeklyQueue


def envelope(ids, now):
    ids = sorted(ids)
    return {
        "fetched_at": now.isoformat(),
        "snapshot": {
            "schema_version": 1,
            "topic_ids": ids,
            "revision": hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest(),
        },
    }


def test_air_spreads_outward_and_returns_to_rest():
    points = air_lattice(AIR_BOUNDS, AIR["spacing"])
    assert air_lattice(AIR_BOUNDS, AIR["spacing"]) is points
    for seconds in (0.4, 1.1, 3.0):
        for point in points:
            (px, py), distance = air_displacement(point, AIR_SOURCE, seconds)
            reach = math.hypot(px - point[0], py - point[1])
            assert reach <= AIR["amplitude"] + 1e-9
            if reach > 1e-6:
                # Motion is along the line from the source, never across it.
                along = abs(
                    (px - point[0]) * (point[1] - AIR_SOURCE[1])
                    - (py - point[1]) * (point[0] - AIR_SOURCE[0])
                )
                assert along / (distance * reach) < 1e-9

    # A finite-speed front does not move distant air immediately, and it only ever
    # travels away from the box: what has started moving never stops having started.
    early = {p for p in points if air_onset(math.dist(p, AIR_SOURCE), 0.2) > 0}
    later = {p for p in points if air_onset(math.dist(p, AIR_SOURCE), 1.4) > 0}
    assert early and early < later and later != set(points)
    reached = max(math.dist(p, AIR_SOURCE) for p in later)
    assert reached <= AIR["speed"] * 1.4

    for t in (0.1, 0.9, 1.0, 2.0, 40.0):
        line = string_points(t, 25, pluck=True)
        assert line[0][1] == pytest.approx(253)
        assert line[-1][1] == pytest.approx(253)


def test_budget_atomic_cap_preservation_and_uncertain_retries(tmp_path):
    ledger = BudgetLedger(tmp_path / "usage.json")
    ledger.initialize_production_task()
    original = ledger.load()
    reserve_request(ledger, "dry", 800, 100000, phase="trial", dry_run=True)
    assert ledger.load() == original
    for i in range(4):
        reserve_request(ledger, str(i), 800, 100000, phase="trial")
    with pytest.raises(BudgetExceeded):
        reserve_request(ledger, "fifth", 800, 100000, phase="trial")
    with pytest.raises(ExternalServiceError):
        reserve_request(ledger, "0", 800, 100000, phase="trial")
    assert ledger.load()["production_v2"]["used"]["tts_characters"] == 3200
    ledger.initialize_production_task()
    assert len(ledger.load()["gemini_v3"]["reservations"]) == 4


def test_voice_identity_changes_only_affected_audio():
    first = SpeechSegment(segment_id="one", text="Waar komt het geluid vandaan?")
    before = speech_identity(first, "nl-NL")
    first.delivery = "curious"
    assert before != speech_identity(first, "nl-NL")
    first.speaker = "bear"
    assert speech_identity(first, "nl-NL")["voice"] != before["voice"]
    with pytest.raises(ValidationError):
        SpeechSegment(segment_id="one", text="test", speaker="eval(__import__)")


def test_queue_priorities_language_retries_and_exhaustion(tmp_path):
    now = datetime.now(UTC)
    q = WeeklyQueue(tmp_path / "private/queue.json")
    topics = {name: "a" * 16 for name in ["a", "b", "c", "d"]}
    first = q.select("2026-09-14", topics, set(), envelope(["a", "b"], now), now=now, seed=1)
    assert first["topic_id"] in {"a", "b"} and first["language"] == "de-DE"
    claimed = q.claim("2026-09-14")
    assert q.select("2026-09-14", topics, set(), None) == claimed
    with pytest.raises(ValueError, match="unfinished"):
        q.select("2026-09-21", topics, set(), envelope(["c"], now), now=now)
    q.finish("2026-09-14", claimed["claim"], error=True)
    retry = q.claim("2026-09-14")
    assert retry["language"] == "de-DE"
    q.finish("2026-09-14", retry["claim"], build_hash="b" * 24, accepted=True)
    second = q.select("2026-09-21", topics, set(), envelope(["a", "b", "c"], now), now=now, seed=1)
    assert second["topic_id"] == "c" and second["language"] == "nl-NL"
    c = q.claim("2026-09-21")
    q.finish("2026-09-21", c["claim"], build_hash="c" * 24, accepted=True)
    with pytest.raises(ValueError, match="exhausted"):
        q.select("2026-09-28", topics, set(topics), envelope([], now), now=now)


def test_queue_missing_stale_malformed_unknown_fail_closed(tmp_path):
    now = datetime.now(UTC)
    q = WeeklyQueue(tmp_path / "queue.json")
    topics = {"a": "a" * 16}
    for data in [None, {}, envelope(["a"], now - timedelta(days=2)), envelope(["unknown"], now)]:
        with pytest.raises(ValueError):
            q.select("2026-09-14", topics, set(), data, now=now)
    assert not q.path.exists()


def test_concurrent_selection_and_claim_cannot_spend_twice(tmp_path):
    now = datetime.now(UTC)
    q = WeeklyQueue(tmp_path / "queue.json")
    topics = {"a": "a" * 16, "b": "b" * 16}
    with ThreadPoolExecutor(max_workers=6) as pool:
        slots = list(
            pool.map(
                lambda _: q.select("2026-09-14", topics, set(), envelope(["a", "b"], now)), range(6)
            )
        )
    assert all(s == slots[0] for s in slots)

    def claim(_):
        try:
            return q.claim("2026-09-14")
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=6) as pool:
        claims = list(pool.map(claim, range(6)))
    assert sum(c is not None for c in claims) == 1


def test_dependency_scope_and_stale_audio_rejection(tmp_path, monkeypatch):
    import erklaerbaer.build_identity as identity
    from tests.factories import make_settings, sample_storyboard

    settings = make_settings(tmp_path)
    board = sample_storyboard()
    original = identity.sha256
    changes = {}
    monkeypatch.setattr(identity, "sha256", lambda p: changes.get(p.name, original(p)))
    before = identity.build_fingerprint(board, settings)
    changes["weekly_queue.py"] = "changed-private-workflow"
    assert identity.build_fingerprint(board, settings) == before
    changes["renderer.py"] = "changed-pixels"
    assert identity.build_fingerprint(board, settings) != before
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"first PCM")
    timing = {"segments": [{"start": 0, "end": 1}]}
    payload = identity.rendered_identity(board, settings, audio, timing)
    key = identity.digest_json(payload)[:24]
    board.review.approved = not board.review.approved
    identity.verify_rendered_identity(board, settings, audio, timing, payload, key)
    audio.write_bytes(b"changed PCM")
    with pytest.raises(ValueError, match="Stale"):
        identity.verify_rendered_identity(board, settings, audio, timing, payload, key)


def test_historical_v2_review_identity_is_preserved():
    from pathlib import Path

    from erklaerbaer.config import load_settings
    from erklaerbaer.models import Storyboard
    from erklaerbaer.science_review import validate_science_review

    root = Path(__file__).parents[1]
    for topic, language, source in [
        ("karton-gitarre", "nl-NL", "7511ac9042e30f1e"),
        ("springende-muenze", "de-DE", "0d6d2f1d3eb3b75d"),
    ]:
        board = Storyboard.model_validate_json(
            (root / f"storyboards/{topic}/{language}/{source}.json").read_text()
        )
        validate_science_review(board, load_settings())


def test_nothing_drawn_for_the_cutaway_crosses_its_rim():
    from erklaerbaer.collage_guitar import CUTAWAY, MEMBRANE_PUSH, cutaway_parts

    stroke = 3  # half of the widest stroke used inside the window
    for step in range(-40, 41):
        push = MEMBRANE_PUSH * step / 40
        top, bottom, membrane, drum = cutaway_parts(push, **CUTAWAY)
        assert drum > CUTAWAY["cx"]
        for x, y in [*top, *bottom, *membrane]:
            radius = math.hypot(x - CUTAWAY["cx"], y - CUTAWAY["cy"])
            assert radius + stroke <= CUTAWAY["radius"]


def test_air_marks_stay_inside_their_field_and_the_frame():
    from erklaerbaer.collage_guitar import (
        AIR_BOUNDS,
        AIR_SOURCE,
        EAR_BOUNDS,
        EAR_SOURCE,
        air_displacement,
        air_lattice,
    )

    for bounds, source in ((AIR_BOUNDS, AIR_SOURCE), (EAR_BOUNDS, EAR_SOURCE)):
        left, top, right, bottom = bounds
        assert left >= 0 and top >= 0 and right <= 1920 and bottom <= 1080
        # A mark may swing by the amplitude and is drawn as a disc of its own radius.
        slack = AIR["amplitude"] + AIR["radius"]
        for seconds in (0.0, 0.7, 2.3, 9.5):
            for point in air_lattice(bounds, AIR["spacing"]):
                (px, py), _ = air_displacement(point, source, seconds)
                assert left - slack <= px <= right + slack
                assert top - slack <= py <= bottom + slack
                assert 0 <= px <= 1920 and 0 <= py <= 1080


def test_internal_silence_is_shortened_but_speech_is_not():
    import numpy as np

    from erklaerbaer.audio import collapse_internal_silence

    rate = 48000
    word = np.sin(np.linspace(0, 400, rate // 2)).astype(np.float32) * 0.4
    quiet = np.zeros(rate * 4, np.float32)
    short = np.zeros(rate // 5, np.float32)
    samples = np.concatenate([word, short, word, quiet, word])
    guard = 0.12
    trimmed = collapse_internal_silence(samples, rate, max_gap=0.6, guard=guard)
    # The four-second pause collapses to the limit plus the guard band kept either side of
    # the words; the fifth-of-a-second pause between words survives untouched.
    assert len(trimmed) < len(samples)
    expected = 0.5 * 3 + 0.2 + 0.6 + 2 * guard
    assert len(trimmed) / rate == pytest.approx(expected, abs=0.05)
    # Nothing loud is ever removed.
    assert float(np.abs(trimmed).max()) == pytest.approx(float(np.abs(samples).max()), abs=1e-6)
    assert int((np.abs(trimmed) > 0.02).sum()) == int((np.abs(samples) > 0.02).sum())


def test_a_repeated_short_line_is_trimmed_but_a_paused_one_is_not():
    import numpy as np

    from erklaerbaer.audio import keep_first_utterance

    rate = 48000

    def tone(seconds):
        return np.sin(np.linspace(0, 400, round(rate * seconds))).astype(np.float32) * 0.4

    gap = np.zeros(round(rate * 0.6), np.float32)
    # "spoken, pause, spoken again": the second reading starts after the line is due.
    repeated = np.concatenate([tone(2.3), gap, tone(2.3)])
    trimmed = keep_first_utterance(repeated, rate, characters=30)
    assert len(trimmed) / rate == pytest.approx(2.3, abs=0.35)

    # One long sentence with an internal pause is left exactly as it is.
    paused = np.concatenate([tone(2.6), gap, tone(2.4)])
    assert len(keep_first_utterance(paused, rate, characters=105)) == len(paused)


def test_no_coin_shot_reaches_the_heading():
    from erklaerbaer.collage_coin import HEADING_FLOOR, VIEWS, View

    for framing in VIEWS:
        view = View(framing)
        # The lid sits above the opening; nothing is drawn higher than it.
        width = (view.mouth[1] - view.mouth[0]) * 1.28
        lid_top = view.mouth[2] - width * 0.30 * 0.55 - 34 * view.scale
        assert lid_top >= HEADING_FLOOR, framing


def test_no_particle_is_ever_drawn_outside_the_bottle():
    from erklaerbaer.collage_coin import PARTICLES, VIEWS, View, gas_points, travelled
    from erklaerbaer.gas import _inside

    for framing in VIEWS:
        view = View(framing)
        for seconds in (0.0, 1.7, 6.4, 19.0, 27.0):
            points = gas_points(view, travelled(seconds, 1.0))
            assert len(points) == PARTICLES
            for x, y in points:
                # The centre stays inside, and the whole mark clears the glass with it.
                assert _inside(view.outline, x, y), (framing, seconds)


def test_german_videos_are_written_in_swiss_spelling():
    from erklaerbaer.models import swiss_spelling

    assert swiss_spelling("Die Flasche bleibt gleich groß.") == "Die Flasche bleibt gleich gross."
    assert swiss_spelling("Stöße und außen") == "Stösse und aussen"
    # Only the sharp s changes; every other letter is left alone.
    assert swiss_spelling("Wärme, Münze, Öffnung") == "Wärme, Münze, Öffnung"
