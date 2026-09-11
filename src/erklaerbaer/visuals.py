from __future__ import annotations

from collections.abc import Iterable

# Deliberately small: each token must have one concrete, child-readable drawing.
VISUAL_TOKEN_VOCABULARY: tuple[str, ...] = (
    "question",
    "stone",
    "lifted-stone",
    "insect",
    "beetle",
    "spider",
    "woodlouse",
    "millipede",
    "worm",
    "water-drop",
    "darkness",
    "shelter",
    "leaf",
    "soil",
    "sprout",
    "zoo-enclosure",
    "bubble",
    "water",
    "coin",
    "bottle",
    "air",
    "heat",
    "pressure",
    "glass",
    "paper",
    "color",
    "guitar",
    "sound-wave",
    "wind",
)


_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("lifted-stone", ("stone_lifted", "lifted_stone", "steen_opgetild")),
    ("woodlouse", ("woodlouse", "assel")),
    ("millipede", ("millipede", "centipede", "duizendpoot", "tausendfuesser")),
    ("spider", ("spider", "spinnen", "spin_legs")),
    ("beetle", ("beetle", "kever")),
    ("insect", ("insect", "six_legs")),
    ("worm", ("worm",)),
    ("stone", ("stone", "rock", "steen")),
    ("water-drop", ("moist", "droplet", "drop", "druppel", "vochtig")),
    ("darkness", ("dark", "donker")),
    ("shelter", ("protect", "safe", "veilig", "shelter", "habitat")),
    ("leaf", ("leaf", "blad")),
    ("soil", ("soil", "ground", "earth", "aarde", "grond")),
    ("sprout", ("sprout", "plant", "nature", "ecosystem", "natuur")),
    ("zoo-enclosure", ("zoo", "enclosure", "dierentuin")),
    ("bubble", ("bubble", "blasen", "bel")),
    ("water", ("water", "liquid", "vloeistof")),
    ("coin", ("coin", "muenze", "münze", "munt")),
    ("bottle", ("bottle", "flasche", "fles")),
    ("heat", ("warm", "heat", "waerme", "wärme", "hitte")),
    ("pressure", ("pressure", "druck", "druk")),
    ("air", ("air", "luft", "lucht")),
    ("glass", ("glass", "glas", "cup")),
    ("paper", ("paper", "papier", "towel", "doek")),
    ("color", ("color", "colour", "farbe", "kleur")),
    ("guitar", ("guitar", "gitarre", "gitaar", "string", "snaar", "cardboard", "karton")),
    ("sound-wave", ("sound", "music", "note", "vibration", "geluid", "trilling")),
    ("wind", ("wind", "turbine", "blade", "fluegel", "vleugel")),
    ("question", ("question", "thought", "pause", "vraag")),
)


def canonical_visual_token(value: str) -> str | None:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    exact = normalized.replace("_", "-")
    if exact in VISUAL_TOKEN_VOCABULARY:
        return exact
    for canonical, aliases in _ALIASES:
        if any(alias in normalized for alias in aliases):
            return canonical
    return None


def normalize_visual_tokens(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        canonical = canonical_visual_token(value)
        if canonical is not None and canonical not in result:
            result.append(canonical)
    return result


def unsupported_visual_tokens(values: Iterable[str]) -> list[str]:
    return [value for value in values if canonical_visual_token(value) is None]
