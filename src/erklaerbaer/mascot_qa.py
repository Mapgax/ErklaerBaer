"""Technical checks for the fixed-step transparent mascot library."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def inspect_library(root: Path) -> dict:
    root = root.resolve()
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest["dimensions"] != [600, 800] or manifest["fps"] != 30:
        raise ValueError("Mascot library must be 600x800 at 30 fps")
    expected = {"neutral", "lift", "explain", "think", "surprise", "aha"}
    if set(manifest["actions"]) != expected:
        raise ValueError("Mascot library must contain exactly six actions")
    report = {"schema_version": 1, "actions": {}, "failures": []}
    global_bounds = []
    first_frames = {}
    for name, action in manifest["actions"].items():
        frames = []
        bounds = []
        coverage = []
        for entry in action["frames"]:
            path = (root / entry["file"]).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Mascot frame escapes library")
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                report["failures"].append(f"{name}: frame checksum mismatch")
            with Image.open(path) as source:
                image = np.asarray(source.convert("RGBA"), dtype=np.int16)
            if image.shape != (800, 600, 4):
                report["failures"].append(f"{name}: invalid frame dimensions")
            alpha = image[..., 3]
            if not np.any(alpha == 0) or not np.any(alpha > 0):
                report["failures"].append(f"{name}: decoded alpha is not mixed")
            coverage.append(float(np.count_nonzero(alpha > 8) / alpha.size))
            ys, xs = np.where(alpha > 8)
            if not len(xs):
                report["failures"].append(f"{name}: empty frame")
                bounds.append((0, 0, 0, 0))
            else:
                bounds.append((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
            frames.append(image)
        first_frames[name] = frames[0]
        global_bounds.extend(bounds)
        final_difference = float(
            np.mean(np.abs(frames[0].astype(float) - frames[-1].astype(float)))
        )
        motion = max(
            float(np.mean(np.abs(frames[0].astype(float) - frame.astype(float))))
            for frame in frames[1:]
        )
        seam = final_difference if action["loop"] else None
        if action["loop"] and seam > 3.0:
            report["failures"].append(f"{name}: loop seam mean error {seam:.2f}")
        if not action["loop"] and len(frames) > 1 and motion < 0.05:
            report["failures"].append(f"{name}: one-shot has no detectable change")
        minimum_coverage = min(coverage)
        if minimum_coverage < 0.05:
            report["failures"].append(
                f"{name}: frame alpha coverage drops to {minimum_coverage:.4f}"
            )
        report["actions"][name] = {
            "frame_count": len(frames),
            "duration_seconds": action["duration"],
            "behavior": action["behavior"],
            "maximum_motion_mean_error": round(motion, 4),
            "first_last_mean_error": round(final_difference, 4),
            "loop_seam_mean_error": None if seam is None else round(seam, 4),
            "minimum_alpha_coverage": round(minimum_coverage, 4),
            "bounds_union": [
                min(box[0] for box in bounds),
                min(box[1] for box in bounds),
                max(box[2] for box in bounds),
                max(box[3] for box in bounds),
            ],
        }
    neutral_first = first_frames["neutral"].astype(float)
    for name in sorted(expected - {"neutral"}):
        difference = float(np.mean(np.abs(first_frames[name].astype(float) - neutral_first)))
        report["actions"][name]["neutral_start_mean_error"] = round(difference, 4)
        if difference < 0.5:
            report["failures"].append(f"{name}: action start is not distinct from neutral")
    union = [
        min(box[0] for box in global_bounds),
        min(box[1] for box in global_bounds),
        max(box[2] for box in global_bounds),
        max(box[3] for box in global_bounds),
    ]
    if union[0] < 2 or union[1] < 2 or union[2] > 597 or union[3] > 797:
        report["failures"].append("Mascot touches the bake-frame edge")
    report["bounds_union"] = union
    report["passed"] = not report["failures"]
    return report
