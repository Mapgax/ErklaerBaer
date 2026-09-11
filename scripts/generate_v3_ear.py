"""One bounded BFL ear illustration; journals stay private and resume without resubmission."""

import hashlib
import json
import os

from erklaerbaer.asset_design import BFLClient
from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.config import load_settings


def main():
    settings = load_settings()
    root = settings.project_root
    out = root / "assets/library/ear/v3"
    out.mkdir(parents=True, exist_ok=True)
    target = out / "ear-source.png"
    if target.exists():
        print("Reusing material sheet")
        return
    if settings.dry_run:
        print("Dry run: one 20-credit BFL reservation; no call")
        return
    ledger = BudgetLedger(root / "catalog/usage.json")
    journal = root / "build/v3/ear.request.json"
    if not journal.exists():
        ledger.reserve("bfl_credits_reserved", 20, 400, dry_run=False)
    else:
        ledger.load()  # Re-read persistent caps before recovering the original request.
    prompt = (
        "One unmistakably recognizable human outer ear (pinna) in side view, as a beautiful "
        "handmade layered paper and softly modelled felt collage illustration for children. "
        "Anatomically recognizable curved outer helix, folded antihelix, concha bowl, small "
        "tragus, subtle dark ear-canal opening facing LEFT, soft rounded earlobe at bottom. "
        "No head, no face, no hair, no person, no jewellery, no hearing aid. "
        "Warm peach and muted terracotta paper, subtle paper fibres, soft restrained relief "
        "and shadows like the reference's tactile quality. Do not copy the bear. "
        "Large centered ear occupying 75 percent of height, all silhouette inside canvas. "
        "Pure perfectly uniform warm off-white background #F5F0E6, no floor shadow. "
        "No letters, numbers, symbols, diagrams, arrows, text, border or watermark."
    )
    reference = root / "assets/mascot/concepts/v1/neutral.png"
    data, info = BFLClient(os.environ["BFL_API_KEY"], journal=journal).generate(
        endpoint=settings.section("asset_design")["endpoint"],
        prompt=prompt,
        reference=reference,
        width=1024,
        height=1024,
        seed=42641,
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
                "semantic_id": "ear-illustration",
                "version": "3",
                "provider": "BFL",
                "model": "flux-2-pro",
                "seed": 42641,
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
