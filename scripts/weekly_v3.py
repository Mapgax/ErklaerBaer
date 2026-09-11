"""Manual private queue preparation only; no production, provider calls or publication."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from erklaerbaer.config import load_settings
from erklaerbaer.models import ExperimentSnapshot
from erklaerbaer.weekly_queue import WeeklyQueue, fetch_favorites


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", required=True, help="Monday ISO date, Europe/Berlin")
    parser.add_argument(
        "--experiments", type=Path, required=True, help="Local public experiments.json"
    )
    parser.add_argument(
        "--snapshot", type=Path, help="Local private feed envelope; never a public source"
    )
    parser.add_argument(
        "--fetch", action="store_true", help="Fetch only the dedicated authenticated feed"
    )
    parser.add_argument(
        "--select", action="store_true", help="Persist selection locally; never claim/spend"
    )
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root
    if args.fetch:
        envelope = fetch_favorites(
            os.environ.get("ERKLAERBAER_FAVORITES_URL", ""),
            os.environ.get("ERKLAERBAER_READ_TOKEN", ""),
        )
    elif args.snapshot:
        envelope = json.loads(args.snapshot.read_text())
    else:
        raise ValueError("A private snapshot or explicit --fetch is required")
    records = json.loads(args.experiments.read_text())
    public = {b.id: b.source_hash for b in map(ExperimentSnapshot.from_mint, records)}
    approval_path = root / "catalog/creative-approvals.json"
    approvals = json.loads(approval_path.read_text()) if approval_path.exists() else {}
    # Exact accepted v3 artifacts are required; a bare catalog status is insufficient.
    covered = set()
    from erklaerbaer.build_identity import verify_rendered_identity
    from erklaerbaer.models import Storyboard

    for path in (root / "artifacts/review-v3/guitar").glob("*/build-identity.json"):
        if path.parent.name not in approvals.get("builds", []):
            continue
        board = Storyboard.model_validate_json((path.parent / "storyboard.json").read_text())
        timing = json.loads((path.parent / "narration.timing.json").read_text())
        verify_rendered_identity(
            board,
            settings,
            path.parent / "narration.wav",
            timing,
            json.loads(path.read_text()),
            path.parent.name,
        )
        covered.add(board.experiment_id)
    queue = WeeklyQueue(root / "private/production/queue.json")
    if not args.select:
        queue.snapshot(envelope, datetime.now(UTC))
        print("Dry run: feed validated. No slot selected; automation remains disabled.")
        return
    if settings.dry_run:
        raise ValueError("--select requires DRY_RUN=false; local selection only")
    selected = queue.select(args.slot, public, covered, envelope)
    # Private state remains on disk; do not print favorite IDs or reasons into shared logs.
    print(f"Local slot saved ({selected['state']}, {selected['language']}). No work started.")


if __name__ == "__main__":
    main()
