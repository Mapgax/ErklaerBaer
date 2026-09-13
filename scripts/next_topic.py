"""Show the next never-used topics for a production slot and freeze the chosen one.

    next_topic.py                         today's slot, five candidates
    next_topic.py --date 2026-09-14       a given slot
    next_topic.py --take backpulver-vulkan   write that topic's MINT snapshot for evidence

Reads only the public MINT library. No provider call.
"""

from __future__ import annotations

import argparse
import json
from datetime import date

from erklaerbaer.config import load_settings
from erklaerbaer.source import MintSource
from erklaerbaer.topics import candidates, slot_language, used_topics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--take", help="topic id to freeze as this slot's evidence snapshot")
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root
    language = slot_language(settings, args.date)
    experiments = MintSource(settings).experiments()
    used = used_topics(root)
    fresh = candidates(experiments, used, args.date)
    if not fresh:
        raise SystemExit("Every MINT topic has been produced; no unused topic remains")
    if args.take:
        if args.take in used or args.take not in experiments:
            raise SystemExit(f"{args.take} is not an unused MINT topic")
        snapshot = experiments[args.take]
        path = root / f"docs/evidence/snapshots/{snapshot.id}-{snapshot.source_hash}.json"
        payload = snapshot.model_dump(mode="json")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "language": language.value,
                    "source_hash": snapshot.source_hash,
                    "snapshot": str(path.relative_to(root)),
                },
                indent=1,
            )
        )
        return
    print(
        f"{args.date.isoformat()} slot: {language.value}; {len(fresh)} unused of {len(experiments)}"
    )
    for snapshot in fresh[: args.count]:
        print(f"- {snapshot.id} [{snapshot.category}] {snapshot.title}: {snapshot.fact[:110]}")


if __name__ == "__main__":
    main()
