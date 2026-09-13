"""Build one registered episode. Speech is the only paid step; --cache-only forbids it.

build_episode.py fall --cache-only      reproduce from cached speech; a miss fails
build_episode.py fall --audio-only      prepare and measure narration, no render
"""

from __future__ import annotations

import argparse

from erklaerbaer.config import load_settings
from erklaerbaer.episode import build_episode
from erklaerbaer.episodes import EPISODES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", choices=sorted(EPISODES))
    parser.add_argument("--cache-only", action="store_true")
    parser.add_argument("--audio-only", action="store_true")
    # Explicit and operator-driven: one retry of a failure the journal recorded.
    parser.add_argument("--retry-failed", action="store_true")
    args = parser.parse_args()
    output = build_episode(
        load_settings(),
        EPISODES[args.episode],
        cache_only=args.cache_only,
        audio_only=args.audio_only,
        retry_failed=args.retry_failed,
    )
    if output:
        print(output)


if __name__ == "__main__":
    main()
