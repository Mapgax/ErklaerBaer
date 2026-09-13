"""Write the Dutch falling-objects storyboard. Authored text, no provider call.

The prose lives here rather than in hand-edited JSON so that duration hints are derived from
the words and pauses, and so the validator runs before anything is written.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

from erklaerbaer.collage_fall import CRUMPLE_PAUSE, RELEASE_PAUSE
from erklaerbaer.models import Storyboard

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HASH = "c120949aca72eba7"
WORDS_PER_MINUTE = 118
SCENE_GAP = 0.45

MECHANISM = {
    "kind": "falling-objects",
    "objects": ["stone", "marble", "paper", "air"],
    "relationships": ["same-release-height", "air-resists-paper"],
}


class Line(NamedTuple):
    speaker: str
    delivery: str
    text: str
    pause_after: float
    beat: str | None


class SceneDraft(NamedTuple):
    framing: str
    primitive: str
    bear: str | None
    heading: str
    anchors: list[str]
    lines: list[tuple]


# Rows are SceneDraft fields in order; each line is a Line in order.
SCENES = [
    (
        "weigh",
        "question",
        "lift",
        "Wat valt het eerst?",
        ["evidence-gravity"],
        [
            ("bear", "curious", "Deze steen is zwaar.", 0.3, "weigh"),
            ("narrator", "warm", "Die glazen knikker is heel licht.", 0.3, None),
            (
                "bear",
                "curious",
                "Als we ze tegelijk laten vallen, welke is dan het eerst beneden?",
                0.3,
                "observe",
            ),
        ],
    ),
    (
        "establish",
        "flow",
        "neutral",
        "Even hoog, tegelijk los",
        ["evidence-gravity"],
        [
            (
                "narrator",
                "warm",
                "We leggen de steen en de knikker naast elkaar op een klep.",
                0.2,
                "observe",
            ),
            ("narrator", "warm", "Ze liggen allebei even hoog boven de grond.", 0.2, "compare"),
            (
                "narrator",
                "warm",
                "Gaat de klep open, dan beginnen ze op precies hetzelfde moment te vallen.",
                0.2,
                "hold",
            ),
        ],
    ),
    (
        "predict",
        "prediction",
        "think",
        "Wat denk jij?",
        ["evidence-gravity"],
        [
            (
                "bear",
                "curious",
                "Valt de zware steen sneller? Of komen ze samen beneden? Wat denk jij?",
                2.8,
                "hold",
            ),
        ],
    ),
    (
        "drop",
        "cause_effect",
        None,
        "Steen tegen knikker",
        ["evidence-gravity"],
        [
            (
                "narrator",
                "warm",
                "We laten het vertraagd zien, zodat je goed kunt kijken.",
                0.3,
                "hold",
            ),
            ("narrator", "warm", "De klep gaat open.", RELEASE_PAUSE, "release"),
            ("narrator", "warm", "Ze raken de grond op hetzelfde moment.", 0.3, "land"),
        ],
    ),
    (
        "landed",
        "comparison",
        "surprise",
        "Tegelijk beneden!",
        ["evidence-gravity", "evidence-galileo"],
        [
            ("bear", "curious", "Tegelijk? Maar de steen is toch veel zwaarder!", 0.4, "land"),
            (
                "narrator",
                "warm",
                "Het klopt toch. Een onderzoeker die Galilei heette, ontdekte dit al "
                "ongeveer vierhonderd jaar geleden.",
                0.2,
                "observe",
            ),
        ],
    ),
    (
        "strobe",
        "comparison",
        None,
        "Steeds sneller, even hoog",
        ["evidence-gravity"],
        [
            (
                "narrator",
                "warm",
                "Hier zie je steeds na een kort moment waar ze allebei zijn.",
                0.3,
                "fall",
            ),
            (
                "narrator",
                "warm",
                "De aarde trekt ze naar beneden. De stukjes worden steeds groter, want ze "
                "vallen steeds sneller.",
                0.3,
                "pull",
            ),
            (
                "narrator",
                "warm",
                "En op elk moment zijn ze even hoog. Zwaar of licht maakt geen verschil.",
                0.2,
                "compare",
            ),
        ],
    ),
    (
        "air",
        "cause_effect",
        None,
        "Blad tegen steen",
        ["evidence-air"],
        [
            (
                "narrator",
                "warm",
                "Nu leggen we een plat blad papier naast de steen.",
                0.3,
                "observe",
            ),
            ("narrator", "warm", "De klep gaat open.", RELEASE_PAUSE, "release"),
            (
                "narrator",
                "warm",
                "De steen is al beneden. Het blad zweeft nog langzaam naar de grond.",
                0.3,
                "land",
            ),
            (
                "narrator",
                "warm",
                "Het platte blad moet veel lucht opzij duwen. Die lucht remt het af.",
                0.2,
                "resist",
            ),
        ],
    ),
    (
        "crumple",
        "cause_effect",
        "explain",
        "Een prop papier",
        ["evidence-air"],
        [
            (
                "narrator",
                "warm",
                "Nu maken we van hetzelfde blad een prop.",
                CRUMPLE_PAUSE,
                "crumple",
            ),
            (
                "narrator",
                "warm",
                "De prop is even zwaar als het blad, maar hij duwt veel minder lucht opzij.",
                0.3,
                "resist",
            ),
            ("narrator", "warm", "De klep gaat open.", RELEASE_PAUSE, "release"),
            (
                "narrator",
                "warm",
                "Nu komen de prop en de steen bijna tegelijk beneden.",
                0.2,
                "land",
            ),
        ],
    ),
    (
        "recap",
        "recap",
        "aha",
        "Zwaar of licht: even snel",
        ["evidence-gravity", "evidence-air"],
        [
            (
                "narrator",
                "satisfied",
                "Zonder remmende lucht vallen zware en lichte dingen even snel.",
                0.3,
                "compare",
            ),
            (
                "narrator",
                "satisfied",
                "Een plat blad duwt veel lucht opzij en zweeft.",
                0.3,
                "resist",
            ),
            (
                "narrator",
                "satisfied",
                "Een prop glipt door de lucht en valt bijna even snel.",
                0.3,
                "fall",
            ),
            ("bear", "satisfied", "Zwaar of licht, dat maakt dus niet uit!", 0.2, "hold"),
        ],
    ),
]


def build() -> dict:
    scenes = []
    for number, draft in enumerate(map(SceneDraft._make, SCENES), 1):
        framing, primitive, bear, heading, anchors, lines = draft
        segments, beats = [], []
        for index, (speaker, delivery, text, pause, beat) in enumerate(map(Line._make, lines), 1):
            segment_id = f"scene-{number}-{index}"
            segments.append(
                {
                    "segment_id": segment_id,
                    "text": text,
                    "pause_after_seconds": pause,
                    "speaker": speaker,
                    "delivery": delivery,
                }
            )
            if beat:
                beats.append({"segment_id": segment_id, "action": beat})
        narration = " ".join(s["text"] for s in segments)
        seconds = len(narration.split()) * 60 / WORDS_PER_MINUTE
        seconds += sum(s["pause_after_seconds"] for s in segments) + SCENE_GAP
        scenes.append(
            {
                "scene_id": f"scene-{number}",
                "mascot": {
                    "visible": bear is not None,
                    "action": bear or "neutral",
                    "height_fraction": 0.72 if framing == "weigh" else 0.65,
                    "placement": "left",
                    "start_seconds": 0.0,
                },
                "segments": segments,
                "mechanism": {**MECHANISM, "beats": beats},
                "primitive": primitive,
                "narration": narration,
                "on_screen_words": [heading],
                "visual_tokens": [],
                "claim_anchors": anchors,
                "sound_cue": "none",
                "duration_hint_seconds": round(max(5.0, seconds), 2),
                "shot": {
                    "template_id": "fall-collage",
                    "version": "3",
                    "framing": framing,
                    "asset_bundle": "fall-v3",
                },
            }
        )
    return {
        "schema_version": "3",
        "template_version": "3",
        "experiment_id": "fall-wettrennen",
        "source_hash": SOURCE_HASH,
        "language": "nl-NL",
        "localized_title": "Wat valt het eerst?",
        "category": "weltraum-physik",
        "scenes": scenes,
        "youtube": {
            "title": "NL | Wat valt het eerst?",
            "description": (
                "Een uitleg over vallen: een zware steen, een lichte knikker en een blad "
                "papier. De stem is gemaakt met tekst-naar-spraak."
            ),
            "tags": [
                "Vallen",
                "Zwaartekracht",
                "Luchtweerstand",
                "Galilei",
                "Natuurkunde",
                "Proefje",
                "Kinderen",
                "Wetenschap",
                "Uitlegvideo",
            ],
            "thumbnail_text": "Wat valt het eerst?",
        },
        "review": {"approved": False, "warnings": []},
        "estimated_duration_seconds": round(sum(s["duration_hint_seconds"] for s in scenes), 2),
    }


def main() -> None:
    board = Storyboard.model_validate(build())
    target = ROOT / f"storyboards/v3/fall-wettrennen/nl-NL/{SOURCE_HASH}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = board.model_dump(mode="json")
    payload.pop("created_at")
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(target, board.estimated_duration_seconds, "s", board.total_words, "words")


if __name__ == "__main__":
    main()
