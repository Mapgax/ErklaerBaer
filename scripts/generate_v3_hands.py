"""One bounded BFL hand illustration for the coin template; journalled and resumable.

One hand is generated and mirrored for the other side, so the pair costs a single request
and is guaranteed symmetric. The prompt asks for a flat known background colour, which lets
the cutout be keyed automatically instead of traced by hand.
"""

from __future__ import annotations

import hashlib
import json
import os

from erklaerbaer.asset_design import BFLClient
from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.config import load_settings

SEED = 42663
BACKGROUND = "#F5F0E6"
PROMPT = (
    "One single human hand of a warm, friendly adult, seen from the back of the hand, "
    "fingers gently curved to the RIGHT as if cupping and warming a jar just out of frame, "
    "thumb tucked below, wrist cut off cleanly at the bottom right with no arm and no sleeve. "
    "Handmade layered paper and softly modelled felt collage illustration for children, "
    "warm peach and muted terracotta papers, subtle paper fibres, soft restrained relief and "
    "gentle shadows, the same tactile handmade quality as the reference. Do not copy the bear, "
    "no bear, no animal, no face, no jewellery, no nail polish, no patterns on the skin. "
    "Large centered hand occupying 80 percent of the canvas, entire silhouette inside canvas. "
    f"Pure perfectly uniform background {BACKGROUND}, no floor shadow, no gradient. "
    "No letters, numbers, symbols, diagrams, arrows, text, border or watermark."
)


def main() -> None:
    settings = load_settings()
    root = settings.project_root
    out = root / "assets/library/hands/v3"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "hand-source.png"
    if target.exists():
        print("Reusing existing hand source")
        return
    if settings.dry_run:
        print("Dry run: one 20-credit BFL reservation; no call was made")
        print(PROMPT)
        return

    ledger = BudgetLedger(root / "catalog/usage.json")
    journal = root / "build/v3/hands.request.json"
    journal.parent.mkdir(parents=True, exist_ok=True)
    if not journal.exists():
        ledger.reserve(
            "bfl_credits_reserved",
            int(settings.section("asset_design")["reserved_credits_per_image"]),
            int(settings.section("asset_design")["monthly_credit_limit"]),
            dry_run=False,
        )
    else:
        ledger.load()  # Re-read persistent caps before recovering the original request.

    reference = root / "assets/mascot/concepts/v1/neutral.png"
    data, info = BFLClient(os.environ["BFL_API_KEY"], journal=journal).generate(
        endpoint=settings.section("asset_design")["endpoint"],
        prompt=PROMPT,
        reference=reference,
        width=1024,
        height=1024,
        seed=SEED,
        output_format="png",
        safety_tolerance=2,
        poll_interval_seconds=2,
        poll_timeout_seconds=240,
    )
    target.write_bytes(data)
    if info["cost"] is not None:
        ledger.record_actual(info["request_id"], "bfl_credits", info["cost"])
    (out / "source.json").write_text(
        json.dumps(
            {
                "semantic_id": "warming-hand",
                "version": "3",
                "provider": "BFL",
                "model": str(settings.section("asset_design")["model"]),
                "seed": SEED,
                "prompt": PROMPT,
                "background": BACKGROUND,
                "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "reserved_credits": 20,
                "actual_credits": info["cost"],
                "review_status": "provisional",
            },
            indent=2,
        )
        + "\n"
    )
    print(target, "| actual credits:", info["cost"])


if __name__ == "__main__":
    main()
