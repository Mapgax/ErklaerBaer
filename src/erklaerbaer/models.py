from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Language(StrEnum):
    GERMAN = "de-DE"
    DUTCH = "nl-NL"

    @property
    def short(self) -> str:
        return "de" if self is Language.GERMAN else "nl"


class ScenePrimitive(StrEnum):
    QUESTION = "question"
    MACRO_TO_MICRO = "macro_to_micro"
    PARTICLES = "particles"
    CAUSE_EFFECT = "cause_effect"
    FLOW = "flow"
    COMPARISON = "comparison"
    PREDICTION = "prediction"
    RECAP = "recap"


class SoundCue(StrEnum):
    NONE = "none"
    CHIME = "chime"
    WHOOSH = "whoosh"
    POP = "pop"
    SPARKLE = "sparkle"


class ExperimentSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    fact: str = Field(min_length=10, max_length=1200)
    observed_result: str = Field(min_length=10, max_length=1600)
    explanation: str = Field(min_length=10, max_length=2400)

    @classmethod
    def from_mint(cls, record: dict[str, Any]) -> ExperimentSnapshot:
        return cls(
            id=record.get("id"),
            title=record.get("titel"),
            category=record.get("kategorie"),
            fact=record.get("fakt"),
            observed_result=record.get("wasPassiert"),
            explanation=record.get("erklaerung"),
        )

    @property
    def source_hash(self) -> str:
        payload = json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]


class MascotAction(StrEnum):
    NEUTRAL = "neutral"
    EXPLAIN = "explain"
    LIFT = "lift"
    THINK = "think"
    SURPRISE = "surprise"
    AHA = "aha"


class MascotShot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    visible: bool = False
    action: MascotAction = MascotAction.NEUTRAL
    placement: str = Field(default="left", pattern=r"^(left|right)$")
    height_fraction: float = Field(default=0.36, ge=0.15, le=0.72)
    start_seconds: float = Field(default=0, ge=0, le=45)


class SpeechSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    segment_id: str = Field(pattern=r"^[a-z0-9-]+$")
    text: str = Field(min_length=1, max_length=300)
    pause_after_seconds: float = Field(default=0.15, ge=0, le=4)
    speaker: str = Field(default="narrator", pattern=r"^(narrator|bear)$")
    delivery: str = Field(default="warm", pattern=r"^(warm|curious|satisfied)$")


class MechanismBeat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    segment_id: str = Field(pattern=r"^[a-z0-9-]+$")
    action: str = Field(
        pattern=(
            r"^(observe|heat|faster|pressure|lift|vent|reset|pluck|vibrate|"
            r"couple|surface|propagate|hear|sound|damp|reveal|insect|spider|woodlouse|compare|hold)$"
        )
    )


class Mechanism(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str = Field(pattern=r"^(gas-pressure|vibrating-string|animal-observation)$")
    objects: list[str] = Field(min_length=1, max_length=8)
    relationships: list[str] = Field(min_length=1, max_length=8)
    beats: list[MechanismBeat] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def known_objects(self):
        allowed = {
            "gas-pressure": (
                {"bottle", "gas", "coin", "heat"},
                {"gas-inside-bottle", "coin-seals-mouth", "heat-to-gas"},
            ),
            "vibrating-string": (
                {"string", "box", "air", "ear"},
                {"string-on-box", "vibration-to-air", "air-to-ear"},
            ),
            "animal-observation": (
                {"stone", "soil", "insect", "spider", "woodlouse"},
                {"animals-under-stone", "compare-leg-pairs"},
            ),
        }
        objects, relations = allowed[self.kind]
        if set(self.objects) != objects or set(self.relationships) != relations:
            raise ValueError("Unsupported mechanism objects or relationships")
        verbs = {
            "gas-pressure": {
                "observe",
                "heat",
                "faster",
                "pressure",
                "lift",
                "vent",
                "reset",
                "hold",
            },
            "vibrating-string": {
                "observe",
                "pluck",
                "vibrate",
                "couple",
                "surface",
                "propagate",
                "hear",
                "sound",
                "damp",
                "hold",
            },
            "animal-observation": {
                "observe",
                "reveal",
                "insect",
                "spider",
                "woodlouse",
                "compare",
                "hold",
            },
        }
        if not all(beat.action in verbs[self.kind] for beat in self.beats):
            raise ValueError("Unsupported action for this mechanism")
        return self


def swiss_spelling(text: str) -> str:
    """Swiss German writes ss where Germany writes ß. House rule for every German video.

    The two spell the same sound, so this changes what a child reads and never how a line
    is spoken.
    """
    return text.replace("ß", "ss").replace("ẞ", "SS")


# A framing names a composition, so it only means anything inside one template.
TEMPLATE_SHOTS = {
    "guitar-collage": (
        "guitar-v3",
        {"establish", "reaction", "string", "attachments", "air", "ear", "decay", "recap"},
    ),
    "coin-collage": (
        "coin-v3",
        {"establish", "micro", "heat", "pressure", "reaction", "lift", "reset", "recap"},
    ),
}


class Shot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    template_id: str = Field(default="guitar-collage", pattern=r"^(guitar-collage|coin-collage)$")
    version: str = Field(default="3", pattern=r"^3$")
    framing: str = Field(pattern=r"^[a-z]+$")
    asset_bundle: str = Field(default="guitar-v3", pattern=r"^(guitar-v3|coin-v3)$")

    @model_validator(mode="after")
    def framing_belongs_to_its_template(self):
        bundle, framings = TEMPLATE_SHOTS[self.template_id]
        if self.framing not in framings:
            raise ValueError(f"Unknown framing {self.framing!r} for {self.template_id}")
        if self.asset_bundle != bundle:
            raise ValueError(f"{self.template_id} requires asset bundle {bundle}")
        return self


class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_id: str = Field(pattern=r"^[a-z0-9-]+$")
    shot: Shot | None = None
    mascot: MascotShot = Field(default_factory=MascotShot)
    segments: list[SpeechSegment] = Field(default_factory=list, max_length=12)
    mechanism: Mechanism | None = None

    @model_validator(mode="after")
    def validate_beats(self):
        if self.segments:
            ids = [segment.segment_id for segment in self.segments]
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate narration segment IDs")
            if " ".join(s.text.strip() for s in self.segments) != self.narration.strip():
                raise ValueError("Narration must equal the ordered segment text")
            if self.mechanism:
                beat_ids = [beat.segment_id for beat in self.mechanism.beats]
                if not set(beat_ids) <= set(ids):
                    raise ValueError("Mechanism beat references missing speech segment")
                if [ids.index(i) for i in beat_ids] != sorted(ids.index(i) for i in beat_ids):
                    raise ValueError("Mechanism beats must follow narration order")
        elif self.mechanism:
            raise ValueError("Mechanisms require explicit narration segments")
        return self

    primitive: ScenePrimitive
    narration: str = Field(min_length=8, max_length=1000)
    on_screen_words: list[str] = Field(default_factory=list, max_length=5)
    visual_tokens: list[str] = Field(default_factory=list, max_length=8)
    claim_anchors: list[str] = Field(min_length=1, max_length=3)
    sound_cue: SoundCue = SoundCue.NONE
    duration_hint_seconds: float = Field(default=15.0, ge=5.0, le=45.0)

    @field_validator("on_screen_words")
    @classmethod
    def validate_words(cls, words: list[str]) -> list[str]:
        if any(not word.strip() or len(word) > 28 for word in words):
            raise ValueError("on-screen words must be non-empty and at most 28 characters")
        if sum(len(word.split()) for word in words) > 5:
            raise ValueError("a scene may show at most five words in total")
        return [word.strip() for word in words]

    @field_validator("visual_tokens", "claim_anchors")
    @classmethod
    def validate_safe_tokens(cls, values: list[str]) -> list[str]:
        forbidden = ("/", "\\", "http:", "https:", "..", "$", "`")
        if any(not value.strip() or len(value) > 40 for value in values):
            raise ValueError("visual tokens must be non-empty and at most 40 characters")
        if any(any(marker in value for marker in forbidden) for value in values):
            raise ValueError("paths, URLs, and shell-like tokens are forbidden")
        return [value.strip() for value in values]

    @field_validator("claim_anchors")
    @classmethod
    def validate_claim_anchors(cls, values: list[str]) -> list[str]:
        allowed = {"fact", "observed_result", "explanation"}
        if not all(value in allowed or value.startswith("evidence-") for value in values):
            raise ValueError("claim anchors must name only approved source fields")
        return values


class YouTubeMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    thumbnail_text: str = Field(min_length=1, max_length=70)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        normalized = [tag.strip() for tag in tags]
        if any(not tag or len(tag) > 30 for tag in normalized):
            raise ValueError("tags must be non-empty and at most 30 characters")
        if sum(len(tag) for tag in normalized) > 450:
            raise ValueError("combined tag text is too long")
        return normalized


class ReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    warnings: list[str] = Field(default_factory=list, max_length=20)


class Storyboard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    template_version: str
    experiment_id: str = Field(pattern=r"^[a-z0-9-]+$")
    source_hash: str = Field(pattern=r"^[a-f0-9]{16}$")
    language: Language
    localized_title: str = Field(min_length=1, max_length=120)
    category: str
    scenes: list[Scene]
    youtube: YouTubeMetadata
    review: ReviewResult
    estimated_duration_seconds: float = Field(ge=1.0, le=600.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_structure(self) -> Storyboard:
        if self.schema_version not in {"1", "2", "3"}:
            raise ValueError("Unsupported storyboard schema")
        if self.schema_version == "3" and self.language is Language.GERMAN:
            # House rule, so a German episode can never ship a ß by accident.
            for scene in self.scenes:
                readable = [*[s.text for s in scene.segments], *scene.on_screen_words]
                if any("ß" in value for value in readable):
                    raise ValueError(f"{scene.scene_id}: German videos use ss, not ß")
            if "ß" in self.youtube.title + self.youtube.description:
                raise ValueError("German videos use ss, not ß")
        # Each v3 template renders one mechanism; a scene may not mix them.
        templates = {"guitar-collage": "vibrating-string", "coin-collage": "gas-pressure"}
        if self.schema_version == "3":
            if any(scene.shot is None or scene.mechanism is None for scene in self.scenes):
                raise ValueError("V3 requires an explicit shot and mechanism in every scene")
            used = {scene.shot.template_id for scene in self.scenes}
            if len(used) != 1:
                raise ValueError("One storyboard uses one v3 template")
            template = used.pop()
            if any(scene.mechanism.kind != templates[template] for scene in self.scenes):
                raise ValueError(f"{template} renders the {templates[template]} mechanism")
        if not 6 <= len(self.scenes) <= 9:
            raise ValueError("storyboard must contain 6 to 9 scenes")
        ids = [scene.scene_id for scene in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("scene IDs must be unique")
        if self.scenes[0].primitive is not ScenePrimitive.QUESTION:
            raise ValueError("first scene must be a question")
        if self.scenes[-1].primitive is not ScenePrimitive.RECAP:
            raise ValueError("last scene must be a recap")
        hinted_seconds = sum(scene.duration_hint_seconds for scene in self.scenes)
        if abs(hinted_seconds - self.estimated_duration_seconds) > 1.0:
            raise ValueError("estimated duration must match the sum of scene duration hints")
        words_per_minute = self.total_words / self.estimated_duration_seconds * 60
        if not 100 <= words_per_minute <= 130:
            raise ValueError("narration pace must be between 100 and 130 words per minute")
        return self

    @property
    def total_words(self) -> int:
        return sum(len(scene.narration.split()) for scene in self.scenes)


class VideoStatus(StrEnum):
    STORYBOARDED = "storyboarded"
    RENDERED = "rendered"
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"
    FAILED = "failed"


class VideoRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experiment_id: str
    language: Language
    source_hash: str
    template_version: str
    status: VideoStatus
    youtube_id: str | None = None
    build_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{24}$")
    storyboard_path: str
    video_sha256: str | None = None
    duration_seconds: float | None = None
    warnings: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def key(self) -> str:
        base = video_key(self.experiment_id, self.language, self.source_hash)
        return f"{base}|{self.build_hash}" if self.build_hash else base


class ReleaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    build_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{24}$")

    date: date
    experiment_id: str
    language: Language
    source_hash: str
    youtube_id: str
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def video_key(self) -> str:
        base = video_key(self.experiment_id, self.language, self.source_hash)
        return f"{base}|{self.build_hash}" if self.build_hash else base


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    current_builds: dict[str, str] = Field(default_factory=dict)
    videos: dict[str, VideoRecord] = Field(default_factory=dict)
    releases: dict[str, ReleaseRecord] = Field(default_factory=dict)


class VideoRequirement(BaseModel):
    date: date
    experiment_id: str
    language: Language
    source_hash: str
    exists: bool


def video_key(experiment_id: str, language: Language, source_hash: str) -> str:
    return f"{experiment_id}|{language.value}|{source_hash}"
