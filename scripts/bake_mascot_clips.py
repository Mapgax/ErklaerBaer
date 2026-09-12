"""Bake one mascot action from a generated clip into the frame library the renderer reads.

The anchor is always a frame of an existing baked rig action, never a concept master. That
is the whole finding of the endpoint probe: anchored on a baked frame the model keeps one
flat ground, and anchored on a concept master it reinvents the bear as a studio photograph.

Geometry is derived, never typed. The placement transform comes from aligning the clip's
own first frame to the anchor it was generated from, and the result is asserted against
that anchor before anything is installed.

  --generate   one paid call, about $0.85 for five seconds at full quality
  --bake       key, resample and fit an already downloaded clip; no network, no spend
  --assemble   write the manifest and run the inspection over the whole library
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import imageio_ffmpeg
import numpy as np
from PIL import Image

from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.config import load_settings
from erklaerbaer.errors import BudgetExceeded
from erklaerbaer.mascot_qa import inspect_library

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_bfl_video import (  # noqa: E402
    PAPER,
    SubmissionRejected,
    _data_uri,
    _download,
    _json_request,
)

SOURCE_RIG = "v4"
TARGET_RIG = "v5"
LIBRARY_FPS = 30
# Below this the key is background; above it the pixel is the bear. Between, it feathers.
SOFT_KEY, HARD_KEY = 6.0, 18.0
# The clip's first frame must land on its anchor to within this, in pixels, or the bake fails.
ANCHOR_TOLERANCE = 6

STYLE = (
    "Keep the supplied frame exactly as it is drawn: the same handmade felt and paper bear, "
    "the same colours, the same edges, the same even lighting. Animate only the character's "
    "own movement. Locked static camera, no camera movement, no zoom, no pan, no parallax. "
    "The background stays one perfectly flat uniform warm off-white field across the whole "
    "clip, with no wall, no floor, no horizon line, no cast shadow, no contact shadow, no "
    "vignette, no photographic studio lighting, no texture and no added scenery. "
    "Do not restyle, relight or re-render the character as a photograph or a 3D object. "
    "No extra characters, no text, no props appearing or disappearing."
)

# One sentence per action, matching what the rig's own timeline was authored to do.
MOTIONS = {
    "lift": (
        "he raises the stone he is already holding a little higher with both paws, looks "
        "down at it with interest, then holds it steady and still. He lifts only the one "
        "stone he is already holding and no other object appears."
    ),
    "explain": (
        "he makes one small calm indicating gesture with his free paw towards the empty "
        "space beside him, as if pointing something out, then lowers the paw slightly and "
        "holds still."
    ),
    "think": (
        "he tilts his head slowly to one side and lowers his gaze in thought, then holds "
        "that attentive pose still. He stays exactly the same size in frame and the top of "
        "his head and the tips of his ears never rise above where they start."
    ),
    "surprise": (
        "his eyebrows rise and his eyes widen in a small gentle moment of surprise, then he "
        "settles and holds still. The reaction happens in the face only. He does not lean, "
        "rear back, hop or straighten up, he stays exactly the same size in frame, and the "
        "top of his head and the tips of his ears never rise above where they start."
    ),
    "aha": (
        "he looks up and raises his free paw in a small, calm, open-palmed gesture of "
        "understanding, then settles and holds still."
    ),
}


def _rig_dir(root: Path, version: str) -> Path:
    return root / "assets/mascot/rig" / version


def _anchor_path(root: Path, action: str) -> Path:
    """The first frame of the baked rig action the clip was generated from."""
    return _rig_dir(root, SOURCE_RIG) / "frames" / action / "0000.png"


def _alpha_bounds(alpha: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(alpha > 8)
    if not len(xs):
        raise ValueError("Frame has no visible character")
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _write_anchor(root: Path, action: str, out_dir: Path) -> Path:
    """Flatten the transparent rig frame onto the paper ground the clip must keep."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(_anchor_path(root, action)) as source:
        frame = source.convert("RGBA")
    flat = Image.new("RGBA", frame.size, PAPER + (255,))
    flat.alpha_composite(frame)
    path = out_dir / f"anchor-{action}.png"
    flat.convert("RGB").save(path)
    return path


def generate(settings, action: str, clip_path: Path) -> None:
    root = settings.project_root
    video = settings.section("video_design")
    if settings.dry_run:
        raise SystemExit("Generating spends money; run with DRY_RUN=false on the invocation")
    api_key = settings.required_env("BFL_API_KEY")["BFL_API_KEY"]
    ledger = BudgetLedger(root / "catalog/usage.json")
    journal = clip_path.with_suffix(".journal.json")
    anchor = _write_anchor(root, action, clip_path.parent)

    submitted: dict[str, Any] | None = None
    if journal.exists():
        saved = json.loads(journal.read_text())
        submitted = saved.get("submitted")
        if not submitted:
            raise SystemExit(f"Uncertain earlier submission for {action}: reconcile {journal}")
        print(f"{action}: recovering the earlier submission rather than resubmitting")
    if submitted is None:
        try:
            projected = ledger.reserve(
                "bfl_video_micro_usd",
                int(video["reserved_micro_usd_per_clip"]),
                int(video["monthly_micro_usd_limit"]),
                dry_run=False,
            )
        except BudgetExceeded as exc:
            raise SystemExit(f"Refusing to call the provider: {exc}") from exc
        print(f"{action}: reserved, month now at {projected} micro-USD")
        payload = {
            "mode": str(video["mode"]),
            "prompt": f"{STYLE} The movement: {MOTIONS[action]}",
            "keyframes": _data_uri(anchor),
            "duration": int(video["duration_seconds"]),
            "aspect_ratio": str(video["aspect_ratio"]),
            "resolution": str(video["resolution"]),
            "generate_audio": bool(video["generate_audio"]),
            "draft": False,
        }
        journal.write_text(json.dumps({"state": "submitting", "action": action}))
        try:
            submitted = _json_request(
                str(video["endpoint"]), api_key, method="POST", payload=payload
            )
        except SubmissionRejected as exc:
            journal.unlink(missing_ok=True)
            raise SystemExit(
                f"{action}: provider refused the body, nothing created:\n{exc}"
            ) from None
        journal.write_text(json.dumps({"state": "polling", "submitted": submitted}))

    polling_url = submitted["polling_url"]
    deadline = time.monotonic() + float(video["poll_timeout_seconds"])
    status_payload: dict[str, Any] = {}
    while time.monotonic() < deadline:
        time.sleep(float(video["poll_interval_seconds"]))
        status_payload = _json_request(polling_url, api_key, method="GET")
        status = str(status_payload.get("status", ""))
        if status == "Ready":
            break
        if status in {"Error", "Failed"}:
            raise SystemExit(f"{action}: generation ended with status {status}")
    else:
        raise SystemExit(f"{action}: generation timed out")

    clip_path.write_bytes(_download(status_payload["result"]["sample"]))
    journal.unlink(missing_ok=True)
    print(f"{action}: {clip_path.name}, {clip_path.stat().st_size} bytes")


def bake(root: Path, action: str, clip_path: Path, anchor_action: str = "") -> dict[str, Any]:
    """Key the clip, resample to the library rate, and fit it onto its own anchor."""
    work = root / "build/v3/clips" / action
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-v",
            "error",
            "-y",
            "-i",
            str(clip_path),
            "-vf",
            f"fps={LIBRARY_FPS}",
            str(work / "%04d.png"),
        ],
        check=True,
    )
    raw = sorted(work.glob("*.png"))

    keyed: list[Image.Image] = []
    for path in raw:
        pixels = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
        # The ground colour comes from the clip's own corners, not from a typed constant.
        corners = np.concatenate(
            [
                pixels[:8, :8].reshape(-1, 3),
                pixels[:8, -8:].reshape(-1, 3),
                pixels[-8:, :8].reshape(-1, 3),
                pixels[-8:, -8:].reshape(-1, 3),
            ]
        )
        ground = np.median(corners, axis=0)
        distance = np.sqrt(((pixels - ground) ** 2).sum(axis=2))
        alpha = np.clip((distance - SOFT_KEY) / (HARD_KEY - SOFT_KEY), 0, 1)
        keyed.append(Image.fromarray(np.dstack([pixels, alpha * 255]).astype(np.uint8), "RGBA"))

    with Image.open(_anchor_path(root, anchor_action or action)) as source:
        anchor = source.convert("RGBA")
    anchor_box = _alpha_bounds(np.asarray(anchor)[..., 3])
    first_box = _alpha_bounds(np.asarray(keyed[0])[..., 3])

    # Scale and placement are read off the anchor pair, so nothing about the fit is typed in.
    scale = (anchor_box[3] - anchor_box[1]) / (first_box[3] - first_box[1])
    anchor_mid = (anchor_box[0] + anchor_box[2]) / 2
    first_mid = (first_box[0] + first_box[2]) / 2
    offset_x = anchor_mid - first_mid * scale
    offset_y = anchor_box[3] - first_box[3] * scale

    out_dir = _rig_dir(root, TARGET_RIG) / "frames" / action
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    for index, frame in enumerate(keyed):
        resized = frame.resize(
            (round(frame.width * scale), round(frame.height * scale)), Image.Resampling.LANCZOS
        )
        canvas = Image.new("RGBA", anchor.size, (0, 0, 0, 0))
        canvas.alpha_composite(resized, (round(offset_x), round(offset_y)))
        canvas.save(out_dir / f"{index:04d}.png")

    installed = sorted(out_dir.glob("*.png"))
    placed = _alpha_bounds(np.asarray(Image.open(installed[0]))[..., 3])
    drift = max(abs(placed[i] - anchor_box[i]) for i in range(4))
    if drift > ANCHOR_TOLERANCE:
        raise SystemExit(
            f"{action}: first frame lands {drift} px from its anchor {anchor_box}, got {placed}"
        )
    boxes = [_alpha_bounds(np.asarray(Image.open(p))[..., 3]) for p in installed]
    union = [
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    ]
    # The renderer crops before compositing, so anything outside the crop is simply cut off.
    crop = json.loads((_rig_dir(root, SOURCE_RIG) / "manifest.json").read_text())["crop"]
    outside = union[0] < crop[0] or union[1] < crop[1] or union[2] > crop[2] or union[3] > crop[3]
    print(f"{action}: {len(installed)} frames, anchor drift {drift} px, bounds {union}")
    if outside:
        print(f"{action}: REJECTED, bounds leave the crop {crop}; regenerate with less movement")
    return {
        "frames": len(installed),
        "anchor_drift": drift,
        "bounds_union": union,
        "inside_crop": not outside,
    }


def assemble(root: Path) -> dict[str, Any]:
    """Neutral is copied from the rig; every other action is a clip. One manifest, one crop."""
    source = json.loads((_rig_dir(root, SOURCE_RIG) / "manifest.json").read_text())
    target_dir = _rig_dir(root, TARGET_RIG)
    neutral_out = target_dir / "frames/neutral"
    if not neutral_out.exists():
        neutral_out.mkdir(parents=True)
        for path in sorted((_rig_dir(root, SOURCE_RIG) / "frames/neutral").glob("*.png")):
            shutil.copy2(path, neutral_out / path.name)

    actions: dict[str, Any] = {}
    for name in source["actions"]:
        files = sorted((target_dir / "frames" / name).glob("*.png"))
        if not files:
            raise SystemExit(f"{name} has not been baked yet")
        loop = name == "neutral"
        actions[name] = {
            "loop": loop,
            "behavior": "loop" if loop else "play-once-hold-last",
            "duration": round(len(files) / LIBRARY_FPS, 4),
            "source": "rig-v4-bake" if loop else "flux-3-video-clip",
            "frames": [
                {
                    "file": f"frames/{name}/{path.name}",
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                for path in files
            ],
        }
    # The crop is a property of the bake it belongs to, so derive it from these frames with
    # the margins the v4 crop kept around v4's own bounds. Recorded, not yet approved: a
    # taller crop renders the bear slightly smaller, which is an owner decision at review.
    boxes = []
    for name in actions:
        for entry in actions[name]["frames"]:
            path = target_dir / entry["file"]
            alpha = np.asarray(Image.open(path))[..., 3]
            rows, cols = np.where(alpha > 8)
            boxes.append((int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())))
    union = [
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    ]
    v4_crop, v4_union = source["crop"], [86, 125, 520, 714]
    margins = [v4_union[i] - v4_crop[i] if i < 2 else v4_crop[i] - v4_union[i] for i in range(4)]
    derived = [
        union[0] - margins[0],
        union[1] - margins[1],
        union[2] + margins[2],
        union[3] + margins[3],
    ]
    inside_v4 = all(
        (union[i] >= v4_crop[i]) if i < 2 else (union[i] <= v4_crop[i]) for i in range(4)
    )
    manifest = {
        "schema_version": 2,
        "dimensions": source["dimensions"],
        "fps": LIBRARY_FPS,
        "pivot": source["pivot"],
        "crop": v4_crop if inside_v4 else derived,
        "crop_source": "inherited from v4" if inside_v4 else "derived from this bake",
        "crop_v4": v4_crop,
        "bounds_union": union,
        "review_status": "provisional-clip-bake",
        "owner_approved": False,
        "anchored_on": f"rig {SOURCE_RIG} first frame of each action",
        "actions": actions,
    }
    (target_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    report = inspect_library(target_dir)
    (target_dir / "mascot-qa.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=sorted(MOTIONS))
    parser.add_argument("--generate", action="store_true", help="One paid call")
    parser.add_argument("--bake", action="store_true", help="Key and fit an existing clip")
    parser.add_argument("--clip", type=Path, help="Use this clip instead of the default path")
    parser.add_argument(
        "--anchor-action",
        choices=("neutral", *sorted(MOTIONS)),
        help="The rig action the clip was actually anchored on, when it is not its own",
    )
    parser.add_argument("--assemble", action="store_true", help="Write the manifest and inspect")
    args = parser.parse_args()

    settings = load_settings()
    root = settings.project_root
    if args.action:
        clip = root / (args.clip or Path(f"build/v3/clips/{args.action}.mp4"))
        clip.parent.mkdir(parents=True, exist_ok=True)
        if args.generate:
            generate(settings, args.action, clip)
        if args.bake:
            bake(root, args.action, clip, args.anchor_action or "")
    if args.assemble:
        report = assemble(root)
        print(json.dumps(report, indent=2))
        if report["failures"]:
            raise SystemExit("Library inspection failed; nothing is installed for production use")


if __name__ == "__main__":
    main()
