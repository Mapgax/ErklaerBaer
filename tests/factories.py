from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from erklaerbaer.config import DEFAULT_CONFIG_PATH, Settings, load_settings
from erklaerbaer.models import (
    ExperimentSnapshot,
    Language,
    ReviewResult,
    Scene,
    ScenePrimitive,
    SoundCue,
    Storyboard,
    YouTubeMetadata,
)


def make_settings(project_root: Path) -> Settings:
    configured = load_settings(DEFAULT_CONFIG_PATH, project_root / "does-not-exist.env")
    return Settings(raw=deepcopy(configured.raw), project_root=project_root)


def sample_experiment(**updates: str) -> ExperimentSnapshot:
    values = {
        "id": "blasen-test",
        "title": "Blasen steigen auf",
        "category": "kuechenchemie",
        "fact": "Gas kann in einer Flüssigkeit viele kleine Blasen bilden.",
        "observed_result": "Die kleinen Blasen steigen nach oben und sammeln sich im Schaum.",
        "explanation": (
            "Gasblasen haben eine geringere Dichte als die Flüssigkeit. Der Auftrieb bewegt sie "
            "nach oben. Im Schaum bleiben viele Blasen vorübergehend in dünnen Flüssigkeitshäuten."
        ),
    }
    values.update(updates)
    return ExperimentSnapshot(**values)


def sample_storyboard(
    language: Language = Language.GERMAN,
    *,
    experiment: ExperimentSnapshot | None = None,
) -> Storyboard:
    source = experiment or sample_experiment()
    primitives = list(ScenePrimitive)
    labels_de = [
        "Warum?",
        "Ganz nah",
        "Gas steigt",
        "Ursache Wirkung",
        "Der Weg",
        "Mehr oder weniger",
        "Was denkst du?",
        "Gas Blase oben",
    ]
    labels_nl = [
        "Waarom?",
        "Heel dichtbij",
        "Gas stijgt",
        "Oorzaak gevolg",
        "De weg",
        "Meer of minder",
        "Wat denk jij?",
        "Gas bel boven",
    ]
    labels = labels_de if language is Language.GERMAN else labels_nl
    narration = (
        "Wir schauen jetzt ganz genau hin und verfolgen gemeinsam Schritt für Schritt, wie das "
        "Gas eine Blase bildet und der Auftrieb diese Blase durch die Flüssigkeit nach oben bewegt."
        if language is Language.GERMAN
        else "We kijken nu heel precies en volgen stap voor stap hoe het gas een bel vormt en hoe "
        "de opwaartse kracht die bel door de vloeistof naar boven beweegt."
    )
    scenes = [
        Scene(
            scene_id=f"scene-{index + 1}",
            primitive=primitive,
            narration=narration,
            on_screen_words=[labels[index]],
            visual_tokens=["bubble", "water"],
            claim_anchors=["explanation"],
            sound_cue=SoundCue.NONE,
            duration_hint_seconds=15,
        )
        for index, primitive in enumerate(primitives)
    ]
    localized_title = (
        "Warum Blasen steigen" if language is Language.GERMAN else "Waarom bellen stijgen"
    )
    title = (
        f"DE | {localized_title} – einfach erklärt"
        if language is Language.GERMAN
        else f"NL | {localized_title} – simpel uitgelegd"
    )
    return Storyboard(
        schema_version="1",
        template_version="1",
        experiment_id=source.id,
        source_hash=source.source_hash,
        language=language,
        localized_title=localized_title,
        category=source.category,
        scenes=scenes,
        youtube=YouTubeMetadata(
            title=title,
            description="Eine kurze Erklärung der sichtbaren Blasen und ihres Auftriebs.",
            tags=["science", "kids", "bubbles"],
            thumbnail_text=localized_title,
        ),
        review=ReviewResult(approved=True),
        estimated_duration_seconds=120,
    )
