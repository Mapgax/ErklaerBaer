"""Every built episode, as data. A new episode adds one entry here and nothing else.

The two published episodes keep the take clean-up and anchor levels they were built with, so
their cached reproduction stays byte-identical. New episodes use CURRENT_TAKES and the
enforced anchor band.
"""

from __future__ import annotations

from . import collage_coin, collage_fall, collage_guitar
from .episode import EpisodeSpec, SoundEvent, TakeCleanup
from .sounds import arrival, clack, crunch, double_knock, escape, knock, pluck, settle, thud

# The guitar was built before take clean-up existed.
GUITAR_TAKES = TakeCleanup()
# The coin trimmed every short line to its first reading.
COIN_TAKES = TakeCleanup(collapse_pauses=True, trim_repeats="short-lines")
# Since the falling-objects pilot: trim only a take too slow to be one reading, and let the
# authored pauses alone decide spacing.
CURRENT_TAKES = TakeCleanup(collapse_pauses=True, trim_repeats="slow-short-lines", edge_silence=0.2)

# Published anchors started right after their segment.
AFTER_SPEECH = 0.05
# A falling-objects landing: the flap opens, then the stone falls the drawn distance.
LANDING = collage_fall.RELEASE_DELAY + collage_fall.FALL_SECONDS
BALL_LANDING = collage_fall.RELEASE_DELAY + collage_fall.FALL_SECONDS * collage_fall.BALL_LAG

EPISODES = {
    "guitar": EpisodeSpec(
        name="guitar",
        storyboard="storyboards/v3/karton-gitarre/nl-NL/7511ac9042e30f1e.json",
        takes=GUITAR_TAKES,
        sound_events=(
            SoundEvent("scene-2-2", AFTER_SPEECH, 0.45, pluck),
            SoundEvent("scene-3-2", AFTER_SPEECH, 0.40, thud),
            SoundEvent("scene-4-2", AFTER_SPEECH, 0.50, arrival),
            SoundEvent("scene-7-2", AFTER_SPEECH, 0.55, pluck, {"gain": 0.05, "decay": 5.0}),
        ),
        thumbnail=collage_guitar.thumbnail,
        anchor_band=None,
    ),
    "coin": EpisodeSpec(
        name="coin",
        storyboard="storyboards/v3/springende-muenze/de-DE/0d6d2f1d3eb3b75d.json",
        takes=COIN_TAKES,
        sound_events=(
            SoundEvent("scene-1-3", AFTER_SPEECH, 0.30, clack),
            SoundEvent("scene-6-1", AFTER_SPEECH, 0.32, clack, {"gain": 0.045}),
            SoundEvent("scene-6-2", AFTER_SPEECH, 0.55, escape),
            SoundEvent("scene-7-1", AFTER_SPEECH, 0.35, settle),
        ),
        thumbnail=collage_coin.thumbnail,
        anchor_band=None,
    ),
    "fall": EpisodeSpec(
        name="fall",
        storyboard="storyboards/v3/fall-wettrennen/nl-NL/c120949aca72eba7.json",
        takes=CURRENT_TAKES,
        sound_events=(
            SoundEvent("scene-4-2", LANDING, collage_fall.KNOCK_SECONDS, double_knock),
            SoundEvent("scene-7-2", LANDING, collage_fall.KNOCK_SECONDS, knock),
            SoundEvent(
                "scene-8-1", collage_fall.CRUMPLE_DELAY, collage_fall.CRUMPLE_SECONDS, crunch
            ),
            SoundEvent(
                "scene-8-3",
                LANDING,
                collage_fall.KNOCK_SECONDS,
                double_knock,
                {"lag": BALL_LANDING - LANDING, "gain": 0.042},
            ),
        ),
        thumbnail=collage_fall.thumbnail,
    ),
}
