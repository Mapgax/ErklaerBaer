from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .asset_design import POSE_NAMES, generate_mascot_concept
from .catalog import CatalogStore
from .config import load_settings
from .doctor import run_doctor
from .errors import ErklaerBaerError
from .models import Language, VideoStatus
from .paths import bundle_paths
from .pipeline import VideoPipeline
from .rive_assets import prepare_rive_assets
from .source import MintSource
from .youtube import setup_youtube


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="erklaerbaer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="validate local and optional online setup")
    doctor.add_argument("--online", action="store_true", help="also contact configured APIs")
    doctor.add_argument("--dry-run", action="store_true")
    doctor.add_argument("--json", action="store_true")

    setup = subparsers.add_parser("setup-youtube", help="authorize a channel and create playlists")
    setup.add_argument("--dry-run", action="store_true")

    mascot = subparsers.add_parser(
        "design-mascot", help="create one bounded BFL mascot concept for the Rive authoring gate"
    )
    mascot.add_argument("--pose", choices=POSE_NAMES, default="neutral")
    mascot.add_argument("--revision", type=int, default=1)
    mascot.add_argument("--reference", type=Path)
    mascot.add_argument("--confirm-max-credits", type=int)
    mascot.add_argument("--dry-run", action="store_true")

    rive_assets = subparsers.add_parser(
        "prepare-rive-assets", help="create transparent authoring assets from approved concepts"
    )
    rive_assets.add_argument("--dry-run", action="store_true")

    discover = subparsers.add_parser("discover", help="report required scheduled video versions")
    discover.add_argument("--days", type=int, default=14)
    discover.add_argument("--start", type=date.fromisoformat)
    discover.add_argument("--dry-run", action="store_true")
    discover.add_argument("--json", action="store_true")

    prepare = subparsers.add_parser(
        "prepare", help="build and privately upload missing versions in the lookahead window"
    )
    prepare.add_argument("--days", type=int, default=14)
    prepare.add_argument("--start", type=date.fromisoformat)
    prepare.add_argument("--dry-run", action="store_true")

    for name, help_text in (
        ("build", "build a local video bundle"),
        ("upload", "build and upload a private draft"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("experiment_id")
        command.add_argument("--language", type=Language, choices=list(Language), required=True)
        command.add_argument("--dry-run", action="store_true")
        command.add_argument(
            "--regenerate-storyboard",
            action="store_true",
            help="explicitly replace a rejected storyboard with a new reviewed attempt",
        )
        command.add_argument(
            "--rerender",
            action="store_true",
            help="reuse the saved storyboard and rebuild narration and local media",
        )

    release = subparsers.add_parser("release", help="release an approved version for one date")
    release.add_argument("--date", type=date.fromisoformat, required=True)
    release.add_argument("--experiment-id", required=True)
    release.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        os.environ["DRY_RUN"] = "true"
    try:
        settings = load_settings()
        if args.command == "doctor":
            checks = run_doctor(settings, online=args.online)
            if args.json:
                print(json.dumps([check.as_dict() for check in checks], indent=2))
            else:
                for check in checks:
                    print(f"{check.status:>4}  {check.name}: {check.detail}")
            return 1 if any(check.status == "FAIL" for check in checks) else 0
        if args.command == "setup-youtube":
            if settings.dry_run:
                print("DRY RUN: OAuth would open locally; no account or .env changes were made.")
                return 0
            result = setup_youtube(settings)
            print("YouTube setup complete: " + ", ".join(sorted(result)))
            return 0
        if args.command == "design-mascot":
            result = generate_mascot_concept(
                settings,
                args.pose,
                reference=args.reference,
                revision=args.revision,
                confirmed_max_credits=args.confirm_max_credits,
            )
            if result.dry_run:
                print(
                    f"DRY RUN: would create {result.pose} mascot at {result.output}; "
                    f"local reserved-credit ceiling {result.reserved_credits}"
                )
            elif result.reused:
                print(f"reused: {result.pose} mascot at {result.output}")
            else:
                charge = (
                    "unknown" if result.actual_credits is None else f"{result.actual_credits:g}"
                )
                print(
                    f"created: {result.pose} mascot at {result.output}; "
                    f"BFL reported {charge} credit(s)"
                )
            return 0
        if args.command == "prepare-rive-assets":
            result = prepare_rive_assets(settings)
            prefix = (
                "DRY RUN: would prepare"
                if result.dry_run
                else ("reused" if result.reused else "prepared")
            )
            print(f"{prefix}: " + ", ".join(str(path) for path in result.outputs))
            return 0
        if args.command == "discover":
            source = MintSource(settings)
            catalog = CatalogStore(settings.project_root / "catalog" / "videos.json")
            start = args.start or _today(settings)
            requirements = source.discover(catalog, start=start, days=args.days)
            if args.json:
                print(json.dumps([item.model_dump(mode="json") for item in requirements], indent=2))
            else:
                for item in requirements:
                    status = "exists" if item.exists else "missing"
                    print(
                        f"{item.date.isoformat()}  {item.language.value}  "
                        f"{item.experiment_id}  {status}  {item.source_hash}"
                    )
                print(f"{len(requirements)} unique required version(s)")
            return 0
        if args.command == "prepare":
            source = MintSource(settings)
            catalog = CatalogStore(settings.project_root / "catalog" / "videos.json")
            start = args.start or _today(settings)
            requirements = source.discover(catalog, start=start, days=args.days)
            cap = int(settings.section("budgets")["max_videos_per_run"])
            pending = []
            for item in requirements:
                record = catalog.find(item.experiment_id, item.language, item.source_hash)
                if record is None or record.status in {
                    VideoStatus.STORYBOARDED,
                    VideoStatus.RENDERED,
                }:
                    pending.append(item)
            selected = pending[:cap]
            if settings.dry_run:
                for item in selected:
                    print(
                        f"DRY RUN: would prepare {item.experiment_id}|"
                        f"{item.language.value}|{item.source_hash}"
                    )
                print(f"{len(selected)} selected; cap {cap}; {len(pending)} pending")
                return 0
            pipeline = VideoPipeline(settings, source=source)
            failures = 0
            for item in selected:
                try:
                    outcome = pipeline.upload(item.experiment_id, item.language)
                    print(
                        f"{outcome.record.status.value}: {item.experiment_id} {item.language.value}"
                    )
                except (ErklaerBaerError, OSError, ValueError, KeyError) as exc:
                    failures += 1
                    print(
                        f"ERROR: {item.experiment_id} {item.language.value}: {exc}", file=sys.stderr
                    )
            return 1 if failures else 0
        if settings.dry_run:
            return _dry_run_external_command(args, settings)
        pipeline = VideoPipeline(settings)
        if args.command == "build":
            outcome = pipeline.build(
                args.experiment_id,
                args.language,
                regenerate_storyboard=args.regenerate_storyboard,
                rerender=args.rerender,
            )
            print(
                f"{outcome.record.status.value}: {outcome.paths.video}"
                + (" (reused)" if outcome.reused else "")
            )
            return 0
        if args.command == "upload":
            outcome = pipeline.upload(
                args.experiment_id,
                args.language,
                regenerate_storyboard=args.regenerate_storyboard,
                rerender=args.rerender,
            )
            print(
                f"{outcome.record.status.value}: YouTube ID {outcome.record.youtube_id}"
                + (" (reused/recovered)" if outcome.reused else "")
            )
            return 0
        if args.command == "release":
            outcome = pipeline.release(args.date, args.experiment_id)
            print(
                f"{outcome.action}: {outcome.language.value}; {outcome.detail}; "
                f"YouTube ID {outcome.youtube_id or '-'}"
            )
            return 0
    except (ErklaerBaerError, OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 2


def _dry_run_external_command(args: argparse.Namespace, settings: object) -> int:
    from .config import Settings

    if not isinstance(settings, Settings):
        raise TypeError("settings must be Settings")
    source = MintSource(settings)
    experiments = source.experiments()
    experiment_id = args.experiment_id
    if experiment_id not in experiments:
        raise ValueError(f"Unknown experiment ID: {experiment_id}")
    experiment = experiments[experiment_id]
    language = settings.language_for_date(args.date) if args.command == "release" else args.language
    catalog = CatalogStore(settings.project_root / "catalog" / "videos.json")
    record = catalog.find(experiment_id, language, experiment.source_hash)
    paths = bundle_paths(settings.project_root, experiment_id, language, experiment.source_hash)
    if args.command == "release":
        if record and record.status is VideoStatus.PUBLIC:
            action = "no-op; current version already public"
        elif record and record.status in {VideoStatus.PRIVATE, VideoStatus.UNLISTED}:
            action = "would query YouTube approval state and publish only if unlisted"
        else:
            action = "would build and upload a private draft; would not publish today"
    elif args.command == "upload":
        action = "would build missing media, recover by content marker, and upload private"
    else:
        action = "would call writer/reviewer, TTS, and local renderer"
    print(
        f"DRY RUN: {action}. key={experiment_id}|{language.value}|{experiment.source_hash}; "
        f"video={paths.video}"
    )
    return 0


def _today(settings: object) -> date:
    from .config import Settings

    if not isinstance(settings, Settings):
        raise TypeError("settings must be Settings")
    timezone = ZoneInfo(str(settings.section("project")["timezone"]))
    return datetime.now(timezone).date()


if __name__ == "__main__":
    raise SystemExit(main())
