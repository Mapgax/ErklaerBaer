# Operating procedure

Current 2026-09-13: two episodes a week are produced by local scheduled tasks following [EPISODE_RUNBOOK.md](EPISODE_RUNBOOK.md). The numbered steps below are the older recovery procedure. Use [RECOVERY_AND_NEXT_STEPS.md](RECOVERY_AND_NEXT_STEPS.md) for exact builds, reproducible commands, spending and continuation order.

1. Read `docs/AGENT_STATUS.md` and the live ledger before resuming. Apply later explicit owner authorizations alongside the original v3 prompt.
2. Preserve sealed artifact directories, native sources, frame libraries and audio caches. Validate the exact review before changing it; do not overwrite identities or edit checksums to suppress failures.
3. For a cached rerender use `scripts/build_episode.py <guitar|coin|fall> --cache-only`. A missing cache is a recovery problem, not permission for new paid calls.
4. Reuse `scripts/build_brand_intro.py` for the 12-second intro and shifted captions. Inspect fades, cached animation loops and the intro-to-episode transition after visual changes.
5. Record any replacement build and review result separately. The YouTube review is `z_1Fx6L3N_Q`; apply its thumbnail after owner phone verification, retaining Private. Do not create duplicates during recovery.
6. Re-read the monthly request and character guards before synthesis.
7. The favourites [queue/feed](WEEKLY_V3.md) is local implementation with an undeployed feed; topic selection uses `scripts/next_topic.py` instead. Public release remains the owner's action.

External data boundaries: approved narration is sent to Google for authorized synthesis, scoped visual prompts/artwork to BFL/Rive, and the explicitly authorized finished review plus metadata to YouTube. This documentation pass makes only read-only requests to official YouTube help. Favorites, private feedback, credentials and ledgers never belong in public media, galleries or handoff ZIPs.

Historical daily operations remain at `archive/OPERATIONS_pre_v3.md`; superseded current text is in the dated recovery archive. Neither is an alternative activation path.
