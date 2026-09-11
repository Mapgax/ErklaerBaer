# Asset and project recovery

Current 2026-09-09. [Full artifact inventory, archive map and continuation](RECOVERY_AND_NEXT_STEPS.md).

## What can be recovered locally

- `assets/mascot/rig/v3/`: repaired embedded `.rev`, `.riv`, six-action PNG library and manifest/QA. Canonical native names are `erklaerbaer-mascot-v3.rev` and `.riv`; original downloads remain in `native/`.
- `native/erklaerbaer-mascot-v3-document-only.rev` is a smaller structural fallback, not a substitute for the full embedded backup.
- Rive IDs: preserve v1 `2558769`, v2 `2561970`, repaired v3 duplicate `2564932` (`ErklaerBaer_Mascot (2)`). Native `.rev` is editable; `.riv` is only a runtime export.
- Fixed crop `[80,118,527,722]` and pivot `[0.5,1.0]` belong to the whole library. Keep authored head bind rotation `-0.10641551025538434`. The actual repair changed neutral contour/UV vertices; do not undo it by resetting the bind pose.
- `assets/library/materials/v3`, `guitar/v3`, `ear/v3`: original artwork/provenance, editable geometry and masks. Guitar native prop Rive files remain missing; SVG/PNG layers do not replace them.
- `artifacts/review-v3/`: exact delivered episode/intro bundles, captions, native bear reel, voice samples, validation and Private upload record.
- `build/audio-cache/`: reusable speech WAVs and identity metadata. Keep this ignored directory to avoid resynthesis. Keep measured narration timing alongside audio.
- `assets/gallery/index.html` and `index.json`: local asset browsing/index; regenerate with `.venv/bin/python3 scripts/index_v3_assets.py` after restoring sources.

The dated documentation archive has an `index.json` mapping original paths to snapshots and hashes. `recovery-inventory.json` beside this guide records exact key deliverable checksums and native file sizes; it is an inventory, not a copy of those assets. Earlier video/code versions remain intact. Do not restore superseded broken intro `49d239b049fb17d0a0ab2b2e` over corrected `fb10cd42eb4001c23272e5ef`.

## Back up without losing recovery state

1. Copy the project code, docs, versioned `assets/`, `storyboards/`, evidence and immutable `artifacts/` to an explicitly chosen owner-controlled backup. Include ignored media and speech caches; a Git clone or code ZIP will omit essential files.
2. Preserve `.env`, external service-account keys, `catalog/usage.json`, provider reservation journals/pending markers, private queue state and owner feedback in a separate encrypted owner backup. These must not enter a public or code-only package. Journals are needed to reconcile uncertain calls; never clear them to make a retry run.
3. Preserve the narrow sibling MINT-Bot changes using its own existing project checkout and backup. The V3 code ZIP is a delta with `ErklaerBaer/` and `MINT-Bot/` roots, not a replacement for either complete project.
4. Keep older versions. A restore must reconcile the newest ledger and in-flight journals; it must not roll usage counters back to an older archive.

No off-machine backup, Git commit or remote archive was created. Most of the checkout is untracked; local archives protect against accidental document edits, not disk loss.

## Restore checks

Restore directories to their original relative paths. Compare `recovery-inventory.json` and each bundle's SHA-256 files. Verify the current runtime and all six action frame paths against `assets/mascot/rig/v3/manifest.json`. Recreate Python 3.12 with `requirements.lock` if required; installing dependencies downloads packages and is separate from offline validation.
Run the exact bundle validator and cache-only reproduction commands in the recovery guide. Missing audio should fail closed. Re-bake only if needed using the pinned official runtime helper and an explicit new `--library` destination, then inspect alpha/rim/crop at video scale. Never replace a missing native source by renaming an older export. Approval belongs to exact reviewed identities and is never inferred from successful recovery.
