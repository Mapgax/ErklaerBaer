from __future__ import annotations

import hashlib
import json
import tempfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, UnidentifiedImageError

from .config import Settings
from .errors import ConfigurationError

APPROVED_POSES = {
    "neutral": "neutral.png",
    "lift": "lifting-stone-r3.png",
    "explain": "explaining.png",
}


@dataclass(frozen=True)
class RiveAssetResult:
    outputs: tuple[Path, ...]
    reused: bool
    dry_run: bool


def prepare_rive_assets(settings: Settings) -> RiveAssetResult:
    version = str(settings.section("asset_design")["concept_version"])
    source_dir = settings.project_root / "assets" / "mascot" / "concepts" / version
    output_dir = settings.project_root / "assets" / "mascot" / "rive-input" / version
    concept_manifest = _read_json(source_dir / "manifest.json")
    concept_outputs = concept_manifest.get("outputs")
    if not isinstance(concept_outputs, dict):
        raise ConfigurationError("Mascot concept manifest has no outputs")

    planned: list[tuple[str, Path, Path]] = []
    for pose, filename in APPROVED_POSES.items():
        key = filename.removesuffix(".png")
        entry = concept_outputs.get(key)
        if not isinstance(entry, dict) or entry.get("review_status") != "approved-by-owner":
            raise ConfigurationError(f"Mascot concept {key} has not passed the owner gate")
        source = source_dir / filename
        if not source.is_file():
            raise ConfigurationError(f"Approved mascot concept is missing: {source}")
        planned.append((pose, source, output_dir / f"pose-{pose}.png"))

    outputs = tuple(item[2] for item in planned)
    if settings.dry_run:
        return RiveAssetResult(outputs=outputs, reused=False, dry_run=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    all_reused = True
    manifest_path = output_dir / "manifest.json"
    existing = _read_json(manifest_path) if manifest_path.exists() else {}
    existing_outputs = existing.get("outputs", {})
    if not isinstance(existing_outputs, dict):
        existing_outputs = {}
    prepared: dict[str, object] = {}
    for pose, source, output in planned:
        source_hash = _sha256(source)
        old = existing_outputs.get(pose)
        can_reuse = (
            output.is_file()
            and isinstance(old, dict)
            and old.get("source_sha256") == source_hash
            and old.get("algorithm") == "connected-border-v5"
        )
        if can_reuse:
            _validate_transparent_png(output)
        else:
            all_reused = False
            _extract_connected_background(source, output)
        prepared[pose] = {
            "source": str(source.relative_to(settings.project_root)),
            "source_sha256": source_hash,
            "output": str(output.relative_to(settings.project_root)),
            "output_sha256": _sha256(output),
            "algorithm": "connected-border-v5",
            "background_distance_threshold": 75,
            "edge_feather_radius": 1.25,
        }
    payload = {
        "schema_version": 1,
        "concept_version": version,
        "purpose": "transparent Rive authoring inputs",
        "outputs": prepared,
    }
    _write_json_atomic(manifest_path, payload)
    return RiveAssetResult(outputs=outputs, reused=all_reused, dry_run=False)


def _extract_connected_background(source: Path, output: Path) -> None:
    try:
        with Image.open(source) as opened:
            rgb_image = opened.convert("RGB")
    except (OSError, UnidentifiedImageError) as exc:
        raise ConfigurationError(f"Invalid mascot source image: {source}") from exc
    rgb = np.asarray(rgb_image, dtype=np.int16)
    height, width, _ = rgb.shape
    side = max(20, width // 32)
    side_samples = np.concatenate((rgb[:, :side, :], rgb[:, -side:, :]), axis=1)
    row_background = np.median(side_samples, axis=1)
    delta = rgb.astype(np.float32) - row_background[:, None, :].astype(np.float32)
    distance = np.sqrt(np.sum(delta * delta, axis=2))
    eligible = distance < 75.0
    red = rgb[:, :, 0]
    green = rgb[:, :, 1]
    blue = rgb[:, :, 2]
    warm_felt = ((red - blue) > 38) & ((red - green) > 18)
    eligible &= ~warm_felt
    eligible[0, :] = True
    eligible[-1, :] = True
    eligible[:, 0] = True
    eligible[:, -1] = True
    connected = _border_connected(eligible, rgb=rgb, max_neighbor_distance=12.0)

    bottom_rows = np.arange(height)[:, None] > int(height * 0.76)
    chroma = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    neutral_floor = bottom_rows & (chroma < 55) & (np.mean(rgb, axis=2) > 80)
    connected |= neutral_floor

    foreground = Image.fromarray((~connected).astype(np.uint8) * 255, mode="L")
    alpha = foreground.filter(ImageFilter.GaussianBlur(radius=1.25))
    alpha_array = np.asarray(alpha, dtype=np.uint8).copy()
    alpha_array[alpha_array < 8] = 0
    alpha_array[alpha_array > 247] = 255
    alpha_array[:3, :] = 0
    alpha_array[-3:, :] = 0
    alpha_array[:, :3] = 0
    alpha_array[:, -3:] = 0
    rgba = np.dstack((rgb.astype(np.uint8), alpha_array))

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output.parent, prefix=f".{output.name}.", suffix=".png", delete=False
    ) as handle:
        temporary = Path(handle.name)
    Image.fromarray(rgba, mode="RGBA").save(temporary, format="PNG", optimize=True)
    temporary.replace(output)
    output.chmod(0o644)
    _validate_transparent_png(output)


def _border_connected(
    eligible: np.ndarray,
    *,
    rgb: np.ndarray | None = None,
    max_neighbor_distance: float | None = None,
) -> np.ndarray:
    height, width = eligible.shape
    connected = np.zeros_like(eligible, dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        if eligible[0, x]:
            connected[0, x] = True
            queue.append((0, x))
        if eligible[height - 1, x] and not connected[height - 1, x]:
            connected[height - 1, x] = True
            queue.append((height - 1, x))
    for y in range(1, height - 1):
        if eligible[y, 0]:
            connected[y, 0] = True
            queue.append((y, 0))
        if eligible[y, width - 1] and not connected[y, width - 1]:
            connected[y, width - 1] = True
            queue.append((y, width - 1))
    while queue:
        y, x = queue.popleft()
        for neighbor_y, neighbor_x in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if not (0 <= neighbor_y < height and 0 <= neighbor_x < width):
                continue
            similar_neighbor = True
            if rgb is not None and max_neighbor_distance is not None:
                color_delta = rgb[neighbor_y, neighbor_x] - rgb[y, x]
                similar_neighbor = float(np.sqrt(np.sum(color_delta * color_delta))) < (
                    max_neighbor_distance
                )
            if (
                eligible[neighbor_y, neighbor_x]
                and not connected[neighbor_y, neighbor_x]
                and similar_neighbor
            ):
                connected[neighbor_y, neighbor_x] = True
                queue.append((neighbor_y, neighbor_x))
    return connected


def _validate_transparent_png(path: Path) -> None:
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG" or image.mode != "RGBA":
                raise ConfigurationError(f"Rive input must be an RGBA PNG: {path}")
            alpha = image.getchannel("A")
            minimum, maximum = alpha.getextrema()
            if minimum != 0 or maximum != 255:
                raise ConfigurationError(f"Rive input needs transparent and opaque pixels: {path}")
            bbox = alpha.getbbox()
            if bbox is None:
                raise ConfigurationError(f"Rive input is fully transparent: {path}")
            left, top, right, bottom = bbox
            if left == 0 or top == 0 or right == image.width or bottom == image.height:
                raise ConfigurationError(
                    f"Rive input foreground touches the canvas boundary: {path}"
                )
    except (OSError, UnidentifiedImageError) as exc:
        raise ConfigurationError(f"Invalid Rive input image: {path}") from exc


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ConfigurationError(f"Invalid JSON object: {path}")
    return payload


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)
    path.chmod(0o644)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
