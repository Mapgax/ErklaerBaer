"""Reproducible, evidence-grounded production scripts. No provider calls."""

# The long lines in this data-authoring script preserve narration segments as reviewable units.
# ruff: noqa: E501

import json
from pathlib import Path

from erklaerbaer.models import Storyboard
from erklaerbaer.storyboards import save_storyboard

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "gas-kinetics": "https://openstax.org/books/chemistry-2e/pages/9-5-the-kinetic-molecular-theory",
    "gas-law": "https://openstax.org/books/college-physics-2e/pages/13-3-the-ideal-gas-law",
    "guitar": "https://newt.phys.unsw.edu.au/music/guitar/guitarintro.html",
    "coupling": "https://phys.unsw.edu.au/music/guitaracoustics/construction.html",
    "sound": "https://openstax.org/books/physics/pages/14-1-speed-of-sound-frequency-and-wavelength",
    "insect": "https://naturalhistory.si.edu/education/teaching-resources/life-science/what-insect",
    "woodlouse": "https://www.wildlifetrusts.org/wildlife-explorer/invertebrates/crustacea-centipedes-and-millipedes/common-woodlouse",
    "legs": "https://www.wildlifetrusts.org/wildlife-explorer/invertebrates/crustacea-centipedes-and-millipedes/pill-woodlouse",
}
DATA = {
    "springende-muenze": {
        "lang": "de-DE",
        "title": "Warum die Münze hüpft",
        "kind": "gas-pressure",
        "objects": ["bottle", "gas", "coin", "heat"],
        "relationships": ["gas-inside-bottle", "coin-seals-mouth", "heat-to-gas"],
        "facts": [
            (
                "evidence-gas",
                "Gas particles are widely separated and move continuously. Higher temperature means greater average kinetic energy. Collisions transfer momentum to container walls.",
                ["gas-kinetics"],
            ),
            (
                "evidence-pressure",
                "With approximately fixed gas amount and rigid container volume, warming raises gas pressure. The coin can lift when the pressure difference supplies enough upward force to overcome its weight and sealing forces. Venting reduces the trapped gas amount and pressure difference; the coin returns.",
                ["gas-law", "gas-kinetics"],
            ),
        ],
        "corrections": [
            "Remove tightly packed cold air: gases remain mostly empty space.",
            "The rigid glass bottle keeps approximately the same volume; the gas pressure rises.",
            "Show a simplified particle model, not literal particle sizes or exact collision trajectories.",
        ],
        "scenes": [
            (
                "question",
                ["Warum hüpft die Münze?"],
                "neutral",
                [
                    ("observe", "Eine Münze liegt auf einer kalten Flasche."),
                    ("heat", "Dann wärmen Hände die Flasche."),
                    ("lift", "Die Münze beginnt zu klacken und hebt sich kurz."),
                    (
                        "observe",
                        "Was bewegt sie? Im Inneren steckt Luft. Wir schauen uns an, wie diese unsichtbare Luft die Münze anheben kann.",
                    ),
                ],
            ),
            (
                "macro_to_micro",
                ["Luft in Bewegung"],
                None,
                [
                    (
                        "observe",
                        "Die Punkte in unserem Bild stehen für winzige Luftteilchen. In Wirklichkeit sind sie viel kleiner und unsichtbar.",
                    ),
                    (
                        "observe",
                        "Zwischen ihnen ist viel freier Raum. Sie bewegen sich ständig und stoßen gegen die Innenwand der Flasche und gegen die Münze.",
                    ),
                ],
            ),
            (
                "cause_effect",
                ["Wärme → schnellere Teilchen"],
                None,
                [
                    (
                        "heat",
                        "Wärme gelangt von den Händen durch das Glas zur Luft. Die Flasche bleibt dabei ungefähr gleich groß.",
                    ),
                    (
                        "faster",
                        "Die wärmere Luft besteht aus denselben Teilchen. Diese bewegen sich jetzt im Durchschnitt schneller. Im Bild zeigen wir das mit schnelleren Punkten.",
                    ),
                ],
            ),
            (
                "particles",
                ["Mehr Druck"],
                None,
                [
                    (
                        "pressure",
                        "Die schnelleren Teilchen übertragen bei ihren Stößen insgesamt mehr Schwung auf die Wände. Der Druck in der Flasche steigt.",
                    ),
                    (
                        "pressure",
                        "Auch von außen drückt Luft gegen die Münze. Entscheidend ist der Unterschied: Innen muss der Druck ausreichend größer werden.",
                    ),
                ],
            ),
            (
                "prediction",
                ["Was passiert als Nächstes?"],
                "think",
                [
                    (
                        "pressure",
                        "Die Münze verschließt die Öffnung noch. Innen ist der Druck gestiegen. Was könnte als Nächstes passieren?",
                    )
                ],
            ),
            (
                "cause_effect",
                ["Heben → Luft entweicht"],
                None,
                [
                    (
                        "lift",
                        "Der zusätzliche Druck von innen kann die Münze gegen ihr Gewicht anheben. Jetzt entsteht ein kleiner Spalt.",
                    ),
                    (
                        "vent",
                        "Durch diesen Spalt entweicht Luft. Dadurch wird der Druckunterschied kleiner. Die Luft bleibt also nicht vollständig in der Flasche eingeschlossen.",
                    ),
                ],
            ),
            (
                "flow",
                ["Die Münze fällt zurück"],
                "surprise",
                [
                    (
                        "reset",
                        "Die Münze fällt zurück auf die Öffnung. Wenn die eingeschlossene Luft weiter erwärmt wird, kann sich der Vorgang wiederholen.",
                    ),
                    (
                        "observe",
                        "Das Klacken ist eine sichtbare und hörbare Folge davon, dass Wärme die Bewegung der Luftteilchen verändert.",
                    ),
                ],
            ),
            (
                "recap",
                ["Wärme · Druck · Bewegung"],
                None,
                [
                    (
                        "heat",
                        "Wärme macht die Luftteilchen im Durchschnitt schneller. Bei ungefähr gleichem Platz steigt der Druck.",
                    ),
                    ("lift", "Die Münze hebt sich."),
                    ("vent", "Luft entweicht, und der Druckunterschied sinkt."),
                    ("reset", "Die Münze fällt zurück. So wird unsichtbare Luftbewegung sichtbar."),
                ],
            ),
        ],
    },
    "karton-gitarre": {
        "lang": "nl-NL",
        "title": "Hoe een kartonnen gitaar klinkt",
        "kind": "vibrating-string",
        "objects": ["string", "box", "air", "ear"],
        "relationships": ["string-on-box", "vibration-to-air", "air-to-ear"],
        "facts": [
            (
                "evidence-vibration",
                "A plucked stretched string vibrates. Oscillation frequency determines pitch. A damped string transfers energy and loses vibration amplitude.",
                ["sound", "guitar"],
            ),
            (
                "evidence-sound",
                "String motion couples through its supports into a guitar body. The body and enclosed air contribute to radiated sound. Air oscillates locally while a pressure disturbance travels outward; the body does not create extra energy.",
                ["coupling", "sound"],
            ),
        ],
        "corrections": [
            "Avoid unsupported generalizations about string thickness or box size.",
            "The box couples vibration to air; it does not create additional energy.",
            "Motion shown at reduced speed; visible vibration frequency is not the actual pitch.",
        ],
        "scenes": [
            (
                "question",
                ["Hoe ontstaat geluid?"],
                "neutral",
                [
                    (
                        "observe",
                        "Een elastiek over een kartonnen doos kan een toon maken. Het lijkt een kleine gitaar. Maar waar komt dat geluid vandaan?",
                    ),
                    (
                        "pluck",
                        "Na een pluk beweegt het elastiek heen en weer. Die beweging is het begin van een reis naar je oren.",
                    ),
                ],
            ),
            (
                "macro_to_micro",
                ["Heen en weer"],
                None,
                [
                    (
                        "vibrate",
                        "We bekijken één elastiek van dichtbij. De uiteinden zitten vast, terwijl het midden heen en weer kan bewegen.",
                    ),
                    (
                        "vibrate",
                        "Dat noemen we trillen. In onze tekening gaat het langzaam, zodat de beweging zichtbaar is. In werkelijkheid kan het elastiek veel sneller trillen.",
                    ),
                ],
            ),
            (
                "cause_effect",
                ["Elastiek → doos"],
                None,
                [
                    (
                        "vibrate",
                        "Het trillende elastiek trekt en duwt aan de plekken waar het op de doos steunt. Zo gaat ook de doos een beetje meetrillen.",
                    ),
                    (
                        "vibrate",
                        "Die beweging is klein. De grote oppervlakken van de doos kunnen de lucht eromheen in beweging brengen.",
                    ),
                ],
            ),
            (
                "flow",
                ["Doos → lucht → oor"],
                None,
                [
                    (
                        "sound",
                        "De trillende doos duwt afwisselend tegen de lucht en beweegt weer terug. Zo ontstaan kleine verschillen in luchtdruk.",
                    ),
                    (
                        "sound",
                        "Die verschillen reizen door de lucht. De luchtdeeltjes bewegen vooral heen en weer rond hun eigen plek. Ze vliegen niet allemaal naar je oor.",
                    ),
                ],
            ),
            (
                "comparison",
                ["Sneller trillen", "hogere toon"],
                None,
                [
                    (
                        "sound",
                        "Bij je oor laat de bewegende lucht je trommelvlies trillen. Zo begint het horen van de toon.",
                    ),
                    (
                        "vibrate",
                        "Hoe vaak het elastiek per seconde trilt, bepaalt de toonhoogte. Vaker heen en weer betekent een hogere toon; minder vaak betekent een lagere toon.",
                    ),
                ],
            ),
            (
                "prediction",
                ["Als de trilling stopt?"],
                "think",
                [
                    (
                        "vibrate",
                        "Stel dat het elastiek niet meer heen en weer beweegt. Zou de toon dan blijven klinken, of juist verdwijnen?",
                    )
                ],
            ),
            (
                "cause_effect",
                ["Trilling neemt af"],
                None,
                [
                    (
                        "damp",
                        "Zonder een nieuwe pluk wordt de trilling steeds kleiner. De bewegingsenergie wordt overgedragen en uiteindelijk onder meer omgezet in warmte.",
                    ),
                    (
                        "damp",
                        "Als het elastiek en de doos tot rust komen, sterft de toon weg. De doos maakte geen nieuwe energie. Ze hielp de trilling door te geven.",
                    ),
                ],
            ),
            (
                "recap",
                ["Elastiek · doos · lucht"],
                "aha",
                [
                    (
                        "pluck",
                        "Eerst trilt het elastiek. Het laat de doos meetrillen, en de doos brengt de lucht in beweging.",
                    ),
                    (
                        "sound",
                        "De verandering in luchtdruk bereikt je oor. Zo wordt een kleine beweging een hoorbare toon.",
                    ),
                ],
            ),
        ],
    },
    "krabbeltier-safari": {
        "lang": "nl-NL",
        "title": "Wie woont er onder een steen?",
        "kind": "animal-observation",
        "objects": ["stone", "soil", "insect", "spider", "woodlouse"],
        "relationships": ["animals-under-stone", "compare-leg-pairs"],
        "facts": [
            (
                "evidence-anatomy",
                "Adult insects have six legs in three pairs. Spiders have eight legs in four pairs and are not insects. Adult woodlice have seven pairs, fourteen legs, and are crustaceans.",
                ["insect", "legs"],
            ),
            (
                "evidence-habitat",
                "Woodlice commonly occupy damp sheltered places such as under stones and feed on decaying plant material. Not every small animal found there is a detritivore. Not every woodlouse species rolls into a ball.",
                ["woodlouse", "legs"],
            ),
        ],
        "corrections": [
            "Do not claim animals occur under almost every stone.",
            "Restrict fourteen legs to adult woodlice.",
            "Do not call all small animals insects or all animals decomposers.",
            "No universal rolling-up claim; no zoo analogy.",
        ],
        "scenes": [
            (
                "question",
                ["Wie zit daar?"],
                "neutral",
                [
                    (
                        "observe",
                        "Onder een steen kan een kleine wereld verborgen zijn. Bij een waarneming kwamen er verschillende kruipende dieren tevoorschijn.",
                    ),
                    (
                        "observe",
                        "Ze zijn allemaal klein, maar horen ze daarom ook bij dezelfde groep? We kijken naar hun lichaamsbouw.",
                    ),
                ],
            ),
            (
                "macro_to_micro",
                ["Een beschutte plek"],
                None,
                [
                    (
                        "reveal",
                        "Als de steen wordt opgetild, wordt zichtbaar wat eronder zit. Ons beeld laat mogelijke bewoners zien; niet onder elke steen zitten dezelfde dieren.",
                    ),
                    (
                        "reveal",
                        "Voor pissebedden is een vochtige, beschutte plek belangrijk. Ze drogen gemakkelijk uit. De ruimte onder een steen kan zo een geschikte schuilplek zijn.",
                    ),
                ],
            ),
            (
                "comparison",
                ["Insect · zes poten"],
                None,
                [
                    (
                        "insect",
                        "Hier staat een volwassen insect. De poten zitten in drie paren aan het middelste deel van zijn lichaam.",
                    ),
                    (
                        "insect",
                        "Drie links en drie rechts: samen zes poten. Ook heeft een insect een kop, een borststuk en een achterlijf.",
                    ),
                ],
            ),
            (
                "comparison",
                ["Spin · acht poten"],
                None,
                [
                    (
                        "spider",
                        "Een spin heeft vier paar poten. Dat zijn er acht: vier aan elke kant. Daarom is een spin geen insect.",
                    ),
                    (
                        "spider",
                        "Klein zijn en over de grond kruipen is dus niet genoeg om bij de insecten te horen. De bouw van het dier geeft betere aanwijzingen.",
                    ),
                ],
            ),
            (
                "comparison",
                ["Pissebed · veertien poten"],
                None,
                [
                    (
                        "woodlouse",
                        "Een volwassen pissebed heeft zeven paar poten. Ze zitten langs het gelede lichaam: zeven links en zeven rechts.",
                    ),
                    (
                        "woodlouse",
                        "Samen zijn dat veertien poten. Een pissebed is een kreeftachtige, geen insect. Jonge pissebedden kunnen nog minder poten hebben.",
                    ),
                ],
            ),
            (
                "prediction",
                ["Zes · acht · veertien"],
                "think",
                [
                    (
                        "compare",
                        "Een dier heeft vier paar poten. Welk dier uit onze vergelijking past daarbij: het insect, de spin of de volwassen pissebed?",
                    )
                ],
            ),
            (
                "cause_effect",
                ["Vier paar → spin"],
                None,
                [
                    (
                        "spider",
                        "Vier paar betekent acht poten. Dat past bij de spin. De pissebed heeft als volwassen dier zeven paar, en het insect drie.",
                    ),
                    (
                        "reveal",
                        "De dieren delen soms een schuilplek, maar niet hetzelfde voedsel. Pissebedden eten bijvoorbeeld verterende plantenresten. Dat geldt niet voor alle kleine bewoners.",
                    ),
                ],
            ),
            (
                "recap",
                ["Kijken", "tellen", "vergelijken"],
                "aha",
                [
                    (
                        "compare",
                        "Een gedeelde schuilplek maakt dieren niet hetzelfde. Hun lichaamsbouw helpt ons verschillen te zien.",
                    ),
                    (
                        "compare",
                        "Een volwassen insect heeft zes poten, een spin acht en een volwassen pissebed veertien. Zo wordt goed kijken een kleine ontdekking.",
                    ),
                ],
            ),
        ],
    },
}


def main():
    for topic, data in DATA.items():
        path = next((ROOT / "storyboards" / topic / data["lang"]).glob("*.json"))
        old = json.loads(path.read_text())
        backup = (
            ROOT
            / "build/production-v2-baseline/storyboards"
            / path.relative_to(ROOT / "storyboards")
        )
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
        pack = {
            "schema_version": 1,
            "experiment_id": topic,
            "source_hash": old["source_hash"],
            "snapshot": f"snapshots/{topic}-{old['source_hash']}.json",
            "facts": [
                {"id": i, "claim": claim, "sources": [SOURCES[k] for k in sources]}
                for i, claim, sources in data["facts"]
            ],
            "corrections": data["corrections"],
            "review_status": "authored-awaiting-independent-review",
        }
        (ROOT / "docs/evidence" / f"{topic}.json").write_text(
            json.dumps(pack, ensure_ascii=False, indent=2) + "\n"
        )
        scenes = []
        for i, (primitive, labels, mascot, beats) in enumerate(data["scenes"], 1):
            sid = f"scene-{i}"
            segments = [
                {
                    "segment_id": f"{sid}-{j}",
                    "text": text,
                    "pause_after_seconds": 2.8 if primitive == "prediction" else 0.2,
                }
                for j, (_, text) in enumerate(beats, 1)
            ]
            narration = " ".join(s["text"] for s in segments)
            scenes.append(
                {
                    "scene_id": sid,
                    "primitive": primitive,
                    "narration": narration,
                    "segments": segments,
                    "mascot": {
                        "visible": bool(mascot),
                        "action": mascot or "neutral",
                        "height_fraction": 0.34,
                        "placement": "left",
                    },
                    "mechanism": {
                        "kind": data["kind"],
                        "objects": data["objects"],
                        "relationships": data["relationships"],
                        "beats": [
                            {"segment_id": s["segment_id"], "action": b[0]}
                            for s, b in zip(segments, beats, strict=True)
                        ],
                    },
                    "on_screen_words": labels,
                    "visual_tokens": [],
                    "claim_anchors": [f[0] for f in data["facts"]],
                    "sound_cue": "none",
                    "duration_hint_seconds": round(len(narration.split()) / 112 * 60, 2),
                }
            )
        old.update(
            schema_version="2",
            template_version="2",
            localized_title=data["title"],
            scenes=scenes,
            review={
                "approved": False,
                "warnings": ["Evidence-grounded revision awaiting independent review"],
            },
            estimated_duration_seconds=sum(s["duration_hint_seconds"] for s in scenes),
        )
        old["youtube"].update(
            title=f"{data['lang'][:2].upper()} | {data['title']}",
            thumbnail_text=data["title"],
            description=(
                "Eine Erklärung der beobachteten Vorgänge. "
                if data["lang"] == "de-DE"
                else "Een uitleg van de waargenomen verschijnselen. "
            )
            + (
                "Die Stimme wurde mit Text-to-Speech erzeugt."
                if data["lang"] == "de-DE"
                else "De stem is gemaakt met tekst-naar-spraak."
            ),
        )
        board = Storyboard.model_validate(old)
        save_storyboard(board, path)
        print(topic, board.total_words, round(board.estimated_duration_seconds, 1))


if __name__ == "__main__":
    main()
