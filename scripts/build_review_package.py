"""Assemble and validate the complete local production-v2 review package."""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from PIL import Image

from erklaerbaer.build_identity import build_fingerprint
from erklaerbaer.catalog import CatalogStore
from erklaerbaer.config import load_settings
from erklaerbaer.mascot_qa import inspect_library
from erklaerbaer.media import sha256_file, validate_media
from erklaerbaer.models import Language, VideoStatus
from erklaerbaer.paths import bundle_paths
from erklaerbaer.storyboards import load_storyboard

PILOTS = (
    ("springende-muenze", Language.GERMAN, "0d6d2f1d3eb3b75d"),
    ("karton-gitarre", Language.DUTCH, "7511ac9042e30f1e"),
    ("krabbeltier-safari", Language.DUTCH, "3b0beaeef4efbdf8"),
)
SRT_TIME = re.compile(r"(?P<start>\d\d:\d\d:\d\d,\d{3}) --> (?P<end>\d\d:\d\d:\d\d,\d{3})")


def _seconds(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, milliseconds = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000


def _validate_srt(path: Path, duration: float) -> dict:
    intervals = [
        (_seconds(match["start"]), _seconds(match["end"]))
        for match in SRT_TIME.finditer(path.read_text(encoding="utf-8"))
    ]
    if not intervals:
        raise ValueError("caption file contains no intervals")
    if any(start < 0 or end <= start for start, end in intervals):
        raise ValueError("caption file contains an invalid interval")
    adjacent = zip(intervals, intervals[1:], strict=False)
    if any(current[1] > following[0] + 0.001 for current, following in adjacent):
        raise ValueError("caption intervals overlap")
    if intervals[-1][1] > duration + 0.25:
        raise ValueError("captions extend beyond the video")
    return {
        "intervals": len(intervals),
        "first_start_seconds": intervals[0][0],
        "last_end_seconds": intervals[-1][1],
    }


def _link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _cost_summary(root: Path) -> dict:
    usage = json.loads((root / "catalog/usage.json").read_text(encoding="utf-8"))
    task = usage["production_v2"]
    used = task["used"]
    limits = task["limits"]
    actual_bfl = sum(
        float(item["amount"])
        for item in usage.get("actual_charges", {}).values()
        if item.get("counter") == "bfl_credits"
    )
    return {
        "used_or_reserved": used,
        "limits": limits,
        "remaining": {name: int(limits[name]) - int(used[name]) for name in limits},
        "actual_bfl_credits": actual_bfl,
        "top_up_or_purchase": False,
    }


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    output = root / "artifacts/review-v2"
    failures: list[str] = []
    report: dict = {
        "schema_version": 1,
        "review_status": "provisional",
        "owner_approved": False,
        "mascot": {},
        "pilots": {},
        "costs": _cost_summary(root),
        "limitations": [
            "The Lift raster contains its held stone; scenes must not add a second lifted stone.",
            "Pronunciation, pacing, child engagement, and creative fit remain owner review items.",
        ],
        "failures": failures,
    }

    rig_root = root / "assets/mascot/rig/v2"
    try:
        mascot = inspect_library(rig_root)
        report["mascot"] = mascot
        failures.extend(f"mascot: {item}" for item in mascot["failures"])
    except Exception as exc:  # report every missing or malformed delivery input together
        failures.append(f"mascot: {type(exc).__name__}: {exc}")

    for required in (
        rig_root / "erklaerbaer-mascot-v2.riv",
        rig_root / "erklaerbaer-mascot-v2.rev",
        rig_root / "manifest.json",
        output / "six-action-reel.mp4",
    ):
        if not required.is_file():
            failures.append(f"missing: {required.relative_to(root)}")

    catalog = CatalogStore(root / "catalog/videos.json")
    for topic, language, source_hash in PILOTS:
        entry: dict = {"language": language.value, "source_hash": source_hash}
        report["pilots"][topic] = entry
        try:
            record = catalog.find(topic, language, source_hash)
            if record is None or not record.build_hash:
                raise ValueError("no fingerprinted current build in catalog")
            if record.status is not VideoStatus.RENDERED:
                raise ValueError(f"current build status is {record.status.value}")
            paths = bundle_paths(root, topic, language, source_hash, record.build_hash)
            current = load_storyboard(paths.storyboard)
            if build_fingerprint(current, settings) != record.build_hash:
                raise ValueError("Stale build: rerender current inputs before packaging")
            media = validate_media(paths.video, settings)
            captions = _validate_srt(paths.captions, media.probe.duration_seconds)
            with Image.open(paths.thumbnail) as thumbnail:
                if thumbnail.size != (1280, 720):
                    raise ValueError(f"thumbnail dimensions are {thumbnail.size}")
            if paths.thumbnail.stat().st_size >= 2_000_000:
                raise ValueError("thumbnail exceeds 2 MB")
            if record.video_sha256 != sha256_file(paths.video):
                raise ValueError("catalog video checksum does not match")
            timing = paths.narration.with_suffix(".timing.json")
            for source, name in (
                (paths.video, "video.mp4"),
                (paths.captions, "captions.srt"),
                (paths.thumbnail, "thumbnail.jpg"),
                (paths.storyboard, "storyboard.json"),
                (timing, "narration.timing.json"),
            ):
                if not source.is_file():
                    raise ValueError(f"missing {source.relative_to(root)}")
                _link_or_copy(source, output / "pilots" / topic / name)
            timing_proof_root = root / "build/production-v2-review" / topic
            for name in ("science-timing-preview.mp4", "science-timing-contact-sheet.jpg"):
                source = timing_proof_root / name
                if not source.is_file():
                    raise ValueError(f"missing {source.relative_to(root)}")
                _link_or_copy(source, output / "pilots" / topic / name)
            entry.update(
                {
                    "build_hash": record.build_hash,
                    "duration_seconds": media.probe.duration_seconds,
                    "resolution": [media.probe.width, media.probe.height],
                    "fps": media.probe.fps,
                    "video_codec": "h264" if media.probe.has_h264 else "unknown",
                    "audio_codec": "aac" if media.probe.has_aac else "unknown",
                    "audio_sample_rate": media.probe.audio_sample_rate,
                    "integrated_lufs": media.loudness.integrated_lufs,
                    "true_peak_dbfs": media.loudness.true_peak_dbfs,
                    "captions": captions,
                    "warnings": list(media.warnings),
                    "passed": True,
                }
            )
        except Exception as exc:  # report every pilot failure in one run
            entry["passed"] = False
            failures.append(f"{topic}: {type(exc).__name__}: {exc}")

    for source in sorted((root / "docs/evidence").glob("*.json")):
        if source.name.endswith(".review.json") or source.stem in {item[0] for item in PILOTS}:
            _link_or_copy(source, output / "evidence" / source.name)
    for source in (
        root / "assets/mascot/rig/rig-contract.json",
        rig_root / "manifest.json",
        rig_root / "mascot-qa.json",
        rig_root / "erklaerbaer-mascot-v2.riv",
        rig_root / "erklaerbaer-mascot-v2.rev",
    ):
        if source.is_file():
            _link_or_copy(source, output / "mascot" / source.name)

    report["passed"] = not failures
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "validation.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown = [
        "# Production v2 local review",
        "",
        f"Overall technical result: **{'PASS' if report['passed'] else 'INCOMPLETE'}**",
        "",
        "Creative status: **provisional; owner sign-off pending**",
        "",
        "## Pilots",
        "",
    ]
    for topic, entry in report["pilots"].items():
        result = "PASS" if entry.get("passed") else "INCOMPLETE"
        duration = f"; {entry['duration_seconds']:.3f} s" if "duration_seconds" in entry else ""
        markdown.append(f"- `{topic}` / `{entry['language']}`: **{result}**{duration}")
    markdown.extend(["", "## Costs", ""])
    costs = report["costs"]
    for name, limit in costs["limits"].items():
        used = costs["used_or_reserved"][name]
        markdown.append(f"- `{name}`: {used} of {limit}; {costs['remaining'][name]} remaining")
    markdown.extend(["", f"Actual BFL charge: {costs['actual_bfl_credits']:g} credits."])
    markdown.extend(["", "## Remaining review items", ""])
    markdown.extend(f"- {item}" for item in report["limitations"])
    markdown.extend(
        [
            "",
            "## Reproduce locally",
            "",
            "The commands below reuse the content-addressed narration cache; "
            "they make no TTS or writer call.",
            "",
            "```bash",
            "DRY_RUN=false .venv/bin/python3 -m erklaerbaer build "
            "springende-muenze --language de-DE --rerender",
            "DRY_RUN=false .venv/bin/python3 -m erklaerbaer build "
            "karton-gitarre --language nl-NL --rerender",
            "DRY_RUN=false .venv/bin/python3 -m erklaerbaer build "
            "krabbeltier-safari --language nl-NL --rerender",
            ".venv/bin/python3 scripts/build_mascot_reel.py",
            ".venv/bin/python3 scripts/build_review_package.py",
            "```",
        ]
    )
    if failures:
        markdown.extend(["", "## Outstanding checks", ""])
        markdown.extend(f"- {failure}" for failure in failures)
    (output / "README.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")

    delivered = [path for path in output.rglob("*") if path.is_file()]
    checksum_lines = [
        f"{sha256_file(path)}  {path.relative_to(output)}"
        for path in sorted(delivered)
        if path.name != "checksums.sha256"
    ]
    (output / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n")
    print(report_path)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
