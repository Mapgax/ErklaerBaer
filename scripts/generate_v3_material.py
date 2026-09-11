"""One bounded BFL material sheet; journals stay private and resume without resubmission."""

import hashlib
import json
import os

from erklaerbaer.asset_design import BFLClient
from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.config import load_settings


def main():
    settings = load_settings()
    root = settings.project_root
    out = root / "assets/library/materials/v3"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "material-sheet.png"
    if target.exists():
        print("Reusing material sheet")
        return
    if settings.dry_run:
        print("Dry run: one 20-credit BFL reservation; no call")
        return
    ledger = BudgetLedger(root / "catalog/usage.json")
    journal = root / "build/v3/material.request.json"
    if not journal.exists():
        ledger.reserve("bfl_credits_reserved", 20, 400, dry_run=False)
    else:
        ledger.load()  # Re-read persistent caps before recovering the original request.
    prompt = (
        "Material texture atlas for layered paper collage science animation, matching the "
        "quiet tactile handmade material quality of the reference. NO bear, NO objects, "
        "NO lettering. Flat overhead view, four equally sized edge-to-edge rectangular "
        "material swatches in a 2 by 2 grid: upper left warm honey tan kraft cardboard "
        "with subtle paper fibres; upper right darker brown corrugated cardboard paper "
        "with very restrained fibres; bottom left soft peach handmade paper; bottom right "
        "muted teal felt. Uniform illumination, restrained fine texture, no gradients, "
        "no folds, no seams within swatches, no highlights, no drop shadows. Full canvas."
    )
    reference = root / "assets/mascot/concepts/v1/neutral.png"
    data, info = BFLClient(os.environ["BFL_API_KEY"], journal=journal).generate(
        endpoint=settings.section("asset_design")["endpoint"],
        prompt=prompt,
        reference=reference,
        width=1024,
        height=1024,
        seed=42640,
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
                "semantic_id": "collage-materials",
                "version": "3",
                "provider": "BFL",
                "model": "flux-2-pro",
                "seed": 42640,
                "prompt": prompt,
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
    print("Material saved; actual credits:", info["cost"])


if __name__ == "__main__":
    main()
