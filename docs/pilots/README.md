# Pilot gate

> For current delivery, subsequent owner authorizations, archives and remaining work, see [Recovery and next steps](../RECOVERY_AND_NEXT_STEPS.md). The original requirements/history below remain preserved.

## V3 benchmark

The owner requires creative revision of the three technically validated v2 pilots. Rebuild the full
Dutch guitar video first using layered paper/felt props, convincing sound transmission, repaired and
better-sized bear, and expressive narrator/bear voices. Deliver it with short voice comparisons and
indexed assets for consolidated review before wider production. Follow
[PRODUCTION_V3_PROMPT.md](../PRODUCTION_V3_PROMPT.md). The earlier board below is historical.

`visual_direction_board.png` is a renderer-produced contact sheet for the four initial category
palettes and language assignments. It contains no generated bitmap artwork and makes no external
API call. Run this from the repository root to regenerate it:

```bash
PYTHONPATH=src:. python3 scripts/create_visual_board.py
```

The first four complete local pilots were generated on 2026-09-05. Their language follows the
scheduled-date parity rule; they have not been uploaded to YouTube.

| Scheduled date | Language | Category | Experiment | Runtime | Local video |
|---|---|---|---|---:|---|
| 2026-09-05 | `nl-NL` | Nature and animals | `krabbeltier-safari` v2 | 106.00 s | `build/krabbeltier-safari/nl-NL/3b0beaeef4efbdf8/video.mp4` |
| 2026-09-06 | `de-DE` | Physics | `springende-muenze` | 102.87 s | `build/springende-muenze/de-DE/0d6d2f1d3eb3b75d/video.mp4` |
| 2026-09-10 | `de-DE` | Kitchen chemistry | `farben-wanderung` | 90.00 s | `build/farben-wanderung/de-DE/fdfc6e0cdf465c9f/video.mp4` |
| 2026-09-13 | `nl-NL` | Technology | `karton-gitarre` | 91.60 s | `build/karton-gitarre/nl-NL/7511ac9042e30f1e/video.mp4` |

Each bundle also has a versioned storyboard, SRT captions, thumbnail, and checksums. Final MP4
and WAV files remain ignored. Presence of these files does not imply creative approval.

Gate 2 asks the owner to assess four dimensions across the set:

1. mascot and paper-cut visual identity;
2. animation density and semantic clarity;
3. pacing and the amount of on-screen text; and
4. German and Dutch Chirp voice suitability.

Record requested changes before Gate 3. A positive Gate 2 decision approves the reusable creative
direction, not every factual sentence in future videos; each uploaded draft still requires human
review.

The `krabbeltier-safari` v2 revision incorporates the first creative review: text-safe
transitions, an animated stone reveal, pose changes for the bear, a controlled literal icon
vocabulary, anatomically correct leg comparisons, and Chirp pace/pause controls. Review frames
are in `artifacts/review/krabbeltier-v2/`.
