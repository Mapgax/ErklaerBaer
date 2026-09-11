from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image, UnidentifiedImageError

from .budgets import BudgetLedger
from .config import Settings
from .errors import ConfigurationError, ExternalServiceError

POSE_NAMES = ("neutral", "lifting-stone", "explaining", "think", "surprise", "aha")

_SHARED_PROMPT = """
Create a polished full-body character concept for the exact original bear scientist shown in the
reference image. Preserve the same identity and proportions: warm medium-brown tactile felt and
paper-cut texture, rounded head, exactly two small rounded ears with dark-brown inner ears, short
cream muzzle,
black oval nose, white expressive eyes, dark curved eyebrows, friendly curious face, sturdy legs
with small toe marks, and a teal neckerchief. The neckerchief must sit naturally around the neck,
with a neat central knot and two short separate tails. The anatomy consists of exactly two ears,
two arms, two paws, and two legs, all fully visible and naturally connected.
Use a lively three-quarter stance, clear layered cut-paper edges, subtle fibers, and soft
directional shadows that give the character real depth while remaining suitable for clean 2D
animation rigging.
Show exactly one bear, centered and fully inside the frame with generous space around every limb,
on a perfectly uniform pale warm-gray background (#F5F0E6). Keep the silhouette and joints easy to
separate into animation layers. No written words, letters, numbers, logos, watermark, border,
checkerboard pattern, scenery, decorative icons, or additional characters.
""".strip()

_POSE_PROMPTS = {
    "think": "A thoughtful curious expression: one eyebrow slightly raised, mouth closed, one paw "
    "resting just beneath the chin, attentive eyes unobscured. Other arm relaxed. "
    "No magnifying glass or other prop. Same face proportions and short teal scarf tails.",
    "surprise": "A visibly surprised but gentle face: both eyebrows raised, eyes wider, a small "
    "round open mouth without teeth. Paws slightly apart beside the torso, "
    "restrained reaction. No props, no extra ears or limbs. Same short teal scarf.",
    "aha": "A visibly understood, satisfied expression: warm closed smile, relaxed eyebrows, "
    "eyes bright and fully visible, one paw raised in a small palm-up acknowledgment. "
    "No props. Exactly the same identity and short teal scarf tails.",
    "neutral": """
Pose: relaxed and alert, weight shifted slightly onto one leg. One paw rests naturally at the hip.
The other paw holds the same teal-rimmed magnifying glass upright beside the face without covering
an eye. Give the bear a small warm smile and an inquisitive eyebrow expression. Arms must connect
clearly at the shoulders and remain visually distinct from the torso. This is the canonical neutral
character master, not a scene.
""".strip(),
    "lifting-stone": """
Pose: the same bear bends slightly at the knees and lifts one broad, low, irregular gray-brown
garden stone with both paws. The stone is at waist height, below the scarf and face. Each complete
arm is readable continuously from its shoulder through its forearm to its paw on the corresponding
edge of the stone. Both legs remain clearly visible and anatomically connected. The bear
looks down toward the empty floor beneath the raised stone with a delighted, curious expression.
The composition contains only the bear and one bare stone. The entire top and underside of the
stone are plain and empty natural rock surfaces. The warm-gray floor and background are empty.
Keep the bear's identity, clothing, colors, textures, body volume, and proportions unchanged.
""".strip(),
    "explaining": """
Pose: the same bear stands upright with an engaged but calm teaching expression. One arm opens in a
welcoming palm-up gesture toward the empty space beside the bear; the other paw points gently toward
that space. Both complete arms, paws, shoulders, and both legs remain clearly visible and
anatomically connected. The mouth is slightly open as if explaining, without visible teeth. Show no
magnifying glass or other prop. Keep the bear's identity, clothing, colors, textures, body volume,
and proportions unchanged.
""".strip(),
}


@dataclass(frozen=True)
class ConceptResult:
    pose: str
    output: Path
    reused: bool
    dry_run: bool
    reserved_credits: int
    actual_credits: float | None = None
    request_id: str | None = None


class BFLClient:
    """Small FLUX.2 client that never logs the API key or expiring result URLs."""

    def __init__(
        self, api_key: str, *, timeout_seconds: float = 60.0, journal: Path | None = None
    ) -> None:
        self.journal = journal
        if not api_key.strip():
            raise ConfigurationError("BFL_API_KEY is required for live mascot design")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def generate(
        self,
        *,
        endpoint: str,
        prompt: str,
        reference: Path,
        width: int,
        height: int,
        seed: int,
        output_format: str,
        safety_tolerance: int,
        poll_interval_seconds: float,
        poll_timeout_seconds: float,
    ) -> tuple[bytes, dict[str, Any]]:
        _validate_bfl_url(endpoint, purpose="submission", allowed_api_only=True)
        payload = {
            "prompt": prompt,
            "disable_pup": True,
            "input_image": base64.b64encode(reference.read_bytes()).decode("ascii"),
            "seed": seed,
            "width": width,
            "height": height,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format,
        }
        submitted = None
        if self.journal and self.journal.exists():
            saved = json.loads(self.journal.read_text())
            submitted = saved.get("submitted")
            if not submitted:
                raise ExternalServiceError("Uncertain BFL submission: reconcile before retrying")
        if submitted is None:
            if self.journal:
                self.journal.parent.mkdir(parents=True, exist_ok=True)
                self.journal.write_text(json.dumps({"state": "submitting"}))
            submitted = self._json_request(endpoint, method="POST", payload=payload)
            if self.journal:
                self.journal.write_text(json.dumps({"state": "polling", "submitted": submitted}))
        request_id = submitted.get("id")
        polling_url = submitted.get("polling_url")
        if not isinstance(request_id, str) or not request_id:
            raise ExternalServiceError("BFL submission response has no request ID")
        if not isinstance(polling_url, str):
            raise ExternalServiceError("BFL submission response has no polling URL")
        _validate_bfl_url(polling_url, purpose="polling")

        deadline = time.monotonic() + poll_timeout_seconds
        status_payload: dict[str, Any] = {}
        while time.monotonic() < deadline:
            time.sleep(poll_interval_seconds)
            status_payload = self._json_request(polling_url, method="GET")
            status = str(status_payload.get("status", ""))
            if status == "Ready":
                break
            if status in {"Error", "Failed"}:
                raise ExternalServiceError(f"BFL generation ended with status {status}")
        else:
            raise ExternalServiceError("BFL generation timed out before an image was ready")

        result = status_payload.get("result")
        sample_url = result.get("sample") if isinstance(result, dict) else None
        if not isinstance(sample_url, str):
            raise ExternalServiceError("BFL ready response has no image URL")
        _validate_bfl_url(sample_url, purpose="download")
        image_bytes = self._binary_request(sample_url)
        metadata = {
            "request_id": request_id,
            "cost": _optional_number(submitted.get("cost")),
            "input_mp": _optional_number(submitted.get("input_mp")),
            "output_mp": _optional_number(submitted.get("output_mp")),
        }
        return image_bytes, metadata

    def _json_request(
        self, url: str, *, method: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "accept": "application/json",
                "Content-Type": "application/json",
                "x-key": self._api_key,
            },
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # noqa: S310
                decoded = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ExternalServiceError(f"BFL HTTP request failed with status {exc.code}") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ExternalServiceError(f"BFL request failed: {type(exc).__name__}") from exc
        if not isinstance(decoded, dict):
            raise ExternalServiceError("BFL returned an invalid JSON response")
        return decoded

    def _binary_request(self, url: str) -> bytes:
        request = Request(url, method="GET", headers={"accept": "image/*"})
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # noqa: S310
                content = response.read(25_000_001)
        except HTTPError as exc:
            raise ExternalServiceError(f"BFL image download failed with status {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise ExternalServiceError(f"BFL image download failed: {type(exc).__name__}") from exc
        if not content or len(content) > 25_000_000:
            raise ExternalServiceError("BFL image download is empty or exceeds 25 MB")
        return content


def generate_mascot_concept(
    settings: Settings,
    pose: str,
    *,
    reference: Path | None = None,
    revision: int = 1,
    confirmed_max_credits: int | None = None,
    client: BFLClient | None = None,
) -> ConceptResult:
    if pose not in POSE_NAMES:
        raise ValueError(f"Unknown mascot pose: {pose}")
    if revision < 1:
        raise ValueError("Mascot concept revision must be positive")
    design = settings.section("asset_design")
    version = "v2" if pose in {"think", "surprise", "aha"} else str(design["concept_version"])
    filename = f"{pose}.png" if revision == 1 else f"{pose}-r{revision}.png"
    output = settings.project_root / "assets" / "mascot" / "concepts" / version / filename
    if output.exists():
        _validate_image(output, int(design["width"]), int(design["height"]))
        return ConceptResult(
            pose, output, reused=True, dry_run=settings.dry_run, reserved_credits=0
        )

    reference_path = reference or _default_reference(settings, pose, version)
    _validate_reference(reference_path)
    reserve = int(design["reserved_credits_per_image"])
    # Conservative whole-MP rounding, using 4.5 credits per input/output MP.
    # Official FLUX.2 pro image-editing pricing checked 2026-09-07.
    with Image.open(reference_path) as reference_image:
        input_mp_bound = math.ceil(reference_image.width * reference_image.height / 1_000_000)
    output_mp_bound = math.ceil(int(design["width"]) * int(design["height"]) / 1_000_000)
    cost_bound = math.ceil(4.5 * (input_mp_bound + output_mp_bound))
    if reserve < cost_bound:
        raise ConfigurationError(f"BFL reserve {reserve} is below cost bound {cost_bound}")
    limit = int(design["monthly_credit_limit"])
    if not settings.dry_run and confirmed_max_credits != reserve:
        raise ConfigurationError(
            f"Live BFL generation requires --confirm-max-credits {reserve}; this is a local "
            "upper-bound acknowledgement, not the expected charge"
        )
    ledger = BudgetLedger(settings.project_root / "catalog" / "usage.json")
    journal = output.with_suffix(".request.json")
    if journal.exists():
        pending = json.loads(journal.read_text())
        if not pending.get("submitted"):
            raise ExternalServiceError("Uncertain BFL submission: reconcile before retrying")
        projected = ledger.current("bfl_credits_reserved")
    else:
        projected = ledger.reserve("bfl_credits_reserved", reserve, limit, dry_run=settings.dry_run)
    if settings.dry_run:
        return ConceptResult(
            pose,
            output,
            reused=False,
            dry_run=True,
            reserved_credits=projected,
        )

    api_key = os.getenv("BFL_API_KEY", "").strip()
    active_client = client or BFLClient(api_key, journal=journal)
    prompt = f"{_SHARED_PROMPT}\n\n{_POSE_PROMPTS[pose]}"
    image_bytes, provider = active_client.generate(
        endpoint=str(design["endpoint"]),
        prompt=prompt,
        reference=reference_path,
        width=int(design["width"]),
        height=int(design["height"]),
        seed=_seed(design, pose, revision),
        output_format="png",
        safety_tolerance=int(design["safety_tolerance"]),
        poll_interval_seconds=float(design["poll_interval_seconds"]),
        poll_timeout_seconds=float(design["poll_timeout_seconds"]),
    )
    if provider.get("cost") is not None:
        ledger.record_actual(str(provider["request_id"]), "bfl_credits", float(provider["cost"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_image_atomic(output, image_bytes)
    _validate_image(output, int(design["width"]), int(design["height"]))
    _update_manifest(
        settings,
        version=version,
        pose=pose,
        prompt=prompt,
        reference=reference_path,
        output=output,
        provider=provider,
        reserved_credits=reserve,
        revision=revision,
    )
    return ConceptResult(
        pose,
        output,
        reused=False,
        dry_run=False,
        reserved_credits=reserve,
        actual_credits=_optional_number(provider.get("cost")),
        request_id=str(provider["request_id"]),
    )


def prompt_for_pose(pose: str) -> str:
    if pose not in POSE_NAMES:
        raise ValueError(f"Unknown mascot pose: {pose}")
    return f"{_SHARED_PROMPT}\n\n{_POSE_PROMPTS[pose]}"


def _default_reference(settings: Settings, pose: str, version: str) -> Path:
    if pose in {"think", "surprise", "aha"}:
        return settings.project_root / "assets/mascot/rive-input/v1/pose-neutral-clean.png"
    if pose == "neutral":
        return settings.project_root / "assets" / "mascot" / "reference" / "chat-mascot.png"
    return settings.project_root / "assets" / "mascot" / "concepts" / version / "neutral.png"


def _validate_reference(path: Path) -> None:
    if not path.is_file():
        raise ConfigurationError(f"Mascot reference not found: {path}")
    try:
        with Image.open(path) as image:
            image.verify()
    except (OSError, UnidentifiedImageError) as exc:
        raise ConfigurationError(f"Mascot reference is not a valid image: {path}") from exc


def _validate_image(path: Path, width: int, height: int) -> None:
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG":
                raise ExternalServiceError("BFL mascot output is not PNG")
            if image.size != (width, height):
                raise ExternalServiceError(
                    f"BFL mascot output is {image.width}x{image.height}; expected {width}x{height}"
                )
    except (OSError, UnidentifiedImageError) as exc:
        raise ExternalServiceError("BFL mascot output is not a valid image") from exc


def _write_image_atomic(path: Path, content: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as file:
        file.write(content)
        temporary = Path(file.name)
    temporary.replace(path)
    path.chmod(0o644)


def _update_manifest(
    settings: Settings,
    *,
    version: str,
    pose: str,
    prompt: str,
    reference: Path,
    output: Path,
    provider: dict[str, Any],
    reserved_credits: int,
    revision: int,
) -> None:
    path = output.parent / "manifest.json"
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        design = settings.section("asset_design")
        payload = {
            "schema_version": 1,
            "concept_version": version,
            "model": str(design["model"]),
            "endpoint_region": "EU",
            "outputs": {},
        }
    outputs = payload.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        raise ValueError("Invalid mascot concept manifest")
    output_key = pose if revision == 1 else f"{pose}-r{revision}"
    outputs[output_key] = {
        "path": str(output.relative_to(settings.project_root)),
        "sha256": _sha256(output),
        "reference_path": str(reference.relative_to(settings.project_root)),
        "reference_sha256": _sha256(reference),
        "prompt": prompt,
        "seed": _seed(settings.section("asset_design"), pose, revision),
        "width": int(settings.section("asset_design")["width"]),
        "height": int(settings.section("asset_design")["height"]),
        "request_id": str(provider["request_id"]),
        "cost_credits": _optional_number(provider.get("cost")),
        "reserved_credits": reserved_credits,
        "input_mp": _optional_number(provider.get("input_mp")),
        "output_mp": _optional_number(provider.get("output_mp")),
        "review_status": "pending",
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_bfl_url(url: str, *, purpose: str, allowed_api_only: bool = False) -> None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not hostname:
        raise ExternalServiceError(f"BFL {purpose} URL must use HTTPS")
    api_hosts = {"api.bfl.ai", "api.eu.bfl.ai", "api.us.bfl.ai"}
    if allowed_api_only and hostname not in api_hosts:
        raise ExternalServiceError(f"BFL {purpose} URL uses an unapproved host")
    if not allowed_api_only and hostname != "bfl.ai" and not hostname.endswith(".bfl.ai"):
        raise ExternalServiceError(f"BFL {purpose} URL uses an unapproved host")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _seed(design: dict[str, Any], pose: str, revision: int) -> int:
    return int(design["seed_base"]) + POSE_NAMES.index(pose) + (revision - 1) * 100


def _optional_number(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def result_as_dict(result: ConceptResult) -> dict[str, object]:
    payload = asdict(result)
    payload["output"] = str(result.output)
    return payload
