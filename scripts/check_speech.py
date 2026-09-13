"""Check prepared narration against its text before anything is rendered.

    check_speech.py fall      after build_episode.py fall --audio-only

Exits non-zero when any take reads faster or slower than one natural reading of its text.
"""

from __future__ import annotations

import argparse
import json

from erklaerbaer.config import load_settings
from erklaerbaer.episode import SINGLE_READING_RATE, reading_rates
from erklaerbaer.episodes import EPISODES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", choices=sorted(EPISODES))
    args = parser.parse_args()
    work = load_settings().project_root / "build/v3" / EPISODES[args.episode].name
    timing = json.loads((work / "narration.timing.json").read_text())
    low, high = SINGLE_READING_RATE
    suspect = []
    for segment_id, rate in reading_rates(work / "narration.wav", timing):
        flag = "" if low <= rate <= high else "  <-- check"
        print(f"{segment_id:12} {rate:5.1f} characters per voiced second{flag}")
        if flag:
            suspect.append(segment_id)
    if suspect:
        raise SystemExit(f"Takes outside one natural reading: {', '.join(suspect)}")


if __name__ == "__main__":
    main()
