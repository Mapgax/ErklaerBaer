"""Offline transparent clips. One-shots clamp; neutral keeps global loop time."""

import json
from pathlib import Path

from PIL import Image

from .models import MascotAction

# Which baked rig generation v3 storyboards use. v3 is the rig the published Dutch episode
# was built from and is kept for exact reproduction; v4 rebinds the magnifier to the torso.
# v5 replaces the five one-shot actions with baked video clips, cropped to the bounds derived
# from that bake; v4 is kept untouched so both published v4 rebuilds stay reproducible.
RIG_VERSION = "v5"


def rig_root(project_root):
    return project_root / "assets/mascot/rig" / RIG_VERSION


# The bear's crop bottom sits on this fraction of frame height in every v3 shot.
MASCOT_BASELINE = 0.86
# Establishing and reaction shots give the bear a little more room from the left edge.
WIDE_FRAMINGS = frozenset({"establish", "reaction"})


def mascot_origin(framing: str, width: int, height: int) -> tuple[int, int]:
    """Left edge and baseline of the composited bear, shared by renderer and templates."""
    fraction = 0.12 if framing in WIDE_FRAMINGS else 0.1
    return round(fraction * width), round(MASCOT_BASELINE * height)


class MascotLibrary:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.manifest = json.loads((root / "manifest.json").read_text())
        if set(self.manifest["actions"]) != {a.value for a in MascotAction}:
            raise ValueError("Six mascot actions required")
        self._cache: dict[tuple[str, int, int], Image.Image] = {}

    def frame_index(self, action: str, seconds: float) -> int:
        spec = self.manifest["actions"][action]
        index = max(0, int(seconds * self.manifest["fps"]))
        return index % len(spec["frames"]) if spec["loop"] else min(index, len(spec["frames"]) - 1)

    def _frame(self, action, index, height):
        cache_key = (action, index, height)
        if cache_key in self._cache:
            return self._cache[cache_key]
        entry = self.manifest["actions"][action]["frames"][index]
        path = (self.root / entry["file"]).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Invalid mascot frame path")
        with Image.open(path) as source:
            im = source.convert("RGBA")
        # Fixed per-library crop, never per-frame, avoids motion-induced anchor jitter.
        if "crop" in self.manifest:
            im = im.crop(tuple(self.manifest["crop"]))
        result = im.resize((round(im.width * height / im.height), height), Image.Resampling.LANCZOS)
        if len(self._cache) >= 160:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = result
        return result

    def frame(self, action, seconds, height):
        return self._frame(action, self.frame_index(action, seconds), height)
