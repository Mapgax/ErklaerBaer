# Local asset recovery

The searchable local gallery is `assets/gallery/index.html`. It runs directly from disk, without
a hosted service, database, CDN or telemetry. `index.json` and per-bundle `bundle.json` retain
semantic IDs, versions, tags, source prompts/model/seed/cost, file checksums, dimensions, actions,
anchors and limitations where available. Pending native exports are explicitly marked missing.

Current source bundles:

- `assets/library/materials/v3`: original BFL material sheet and provenance.
- `assets/library/guitar/v3`: layered SVG, independent geometry SVG, RGBA layers and preview.
- `assets/library/ear/v3`: original BFL illustration, editable silhouette SVG/mask and RGBA export.
- `assets/mascot/rig/v2`: complete historical native `.rev`/`.riv` and fixed-step frames.
- `assets/mascot/rig/v3`: provisional copied frames with fixed crop `[80,118,527,722]`; pending
  native repair/export. These must never be mistaken for a repaired v3 native runtime.

Preserve v1 master 2558769, v2 working file 2561970, the new recoverable duplicate 2564932 and all
historical native exports. The rim repair script records old/new geometry and UV values so its
narrow edit can be restored. It deliberately refuses to act on v1/v2.

## Backup procedure

1. Copy `assets/` and accepted immutable `artifacts/` to an owner-controlled backup drive, keeping
   version directory names. Preserve each checksum/manifest. Do not overwrite prior versions.
2. Separately back up the ignored `build/audio-cache/` and measured timing metadata if cache-only
   rerenders are needed. Exclude request journals and pending markers from an artwork handoff.
3. Keep `.env`, credentials, `catalog/usage.json`, provider journals, private queue data and owner
   feedback in a separate encrypted owner backup. These do not belong in the asset gallery,
   code-only archive or public release. Never reset the usage ledger when restoring assets.
4. No remote backup/upload has been performed by this task. Choose a private backup destination
   explicitly before copying anything outside the authorized local workspace.

## Restore and validate

Restore version directories intact, verify SHA-256 against each bundle's file map, and run the
mascot QA before compositing. Native `.rev` is the editable recovery source; `.riv` is a runtime
export, not an authoring backup. Re-bake with the pinned official runtime helper when needed,
using an explicit new `--library` directory. Production rendering uses the resulting local clips,
not a live cloud Rive dependency.

Regenerate the local gallery with `.venv/bin/python3 scripts/index_v3_assets.py`. Never make a
missing native export pass by renaming a historical runtime. A render/package validator must
reject missing, changed or stale content. Record creative approval separately against the exact
build and asset identities; do not edit asset bytes to record approval.
