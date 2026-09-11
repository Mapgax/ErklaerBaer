"""Synthesize a reviewed pilot once; all later visual work uses this segment cache."""

import argparse

from erklaerbaer.audio import GoogleNarrator
from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.captions import save_segment_srt
from erklaerbaer.config import load_settings
from erklaerbaer.science_review import validate_science_review
from erklaerbaer.storyboards import load_storyboard

parser = argparse.ArgumentParser()
parser.add_argument("topic")
parser.add_argument("language")
args = parser.parse_args()
settings = load_settings()
root = settings.project_root
board = load_storyboard(next((root / "storyboards" / args.topic / args.language).glob("*.json")))
validate_science_review(board, settings)
out = root / "build/production-v2-review" / args.topic
out.mkdir(parents=True, exist_ok=True)
r = GoogleNarrator(settings, BudgetLedger(root / "catalog/usage.json")).synthesize(
    board, out / "narration.wav"
)
save_segment_srt(r.segments, out / "captions.srt")
print(
    {
        "topic": args.topic,
        "seconds": r.total_seconds,
        "new_tts_characters": r.character_count,
        "segments": len(r.segments),
    },
    flush=True,
)
