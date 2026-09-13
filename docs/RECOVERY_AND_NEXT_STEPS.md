# Recovery and next steps

Verified handoff: 2026-09-09. Paths below are relative to the ErklaerBaer project root.

## Start here after reopening or restoring the project

1. Read this guide, then `docs/AGENT_STATUS.md` and the original authority in `docs/PRODUCTION_V3_PROMPT.md`.
2. Review the current video: https://youtu.be/D-HipNUmOOA (episode `88b41b6568bd1dbc709bcd66`, 6-second intro, 181.03 s). The superseded cut is https://youtu.be/z_1Fx6L3N_Q. It is saved Private on channel `UC3yza3Tcu5vyNwr661Uai6g`, shown as Andreas Döpfert / @Papa_baer_andreas. Notifications are disabled; Dutch captions are uploaded. The channel has not been renamed to ErklaerBaer.
3. Read `artifacts/review-v3/youtube-private-upload.json` for the observed upload result and `artifacts/review-v3/validation.json` for technical evidence.
4. Read `catalog/usage.json` before any paid operation. Restoring files or opening a new task never resets the allowance.

## Delivered and preserved

| Item | Exact location / identity | State |
|---|---|---|
| Full review, intro + guitar | `artifacts/review-v3/intro/fb10cd42eb4001c23272e5ef/full-review.mp4` | 187.03 seconds locally; YouTube displays 3:08; Private upload verified |
| Reusable intro | Same folder, `intro.mp4`, `jingle.wav`, `manifest.json` | 12 seconds; original local additive synthesis, no samples/drums/provider calls |
| Full Dutch guitar episode | `artifacts/review-v3/guitar/cedfada8807f70f3fe6b4a2c/` | 175.03 seconds, 1080p/30 fps, Gemini Sulafat narrator and revised Achird bear delivery |
| Captions | Episode folder `captions.srt`; intro folder `captions.srt` | 15 intervals; combined version shifted by 12 seconds |
| Thumbnail | Episode folder `thumbnail.jpg` | Prepared locally; custom upload blocked by channel phone verification |
| Corrected native bear | `assets/mascot/rig/v3/erklaerbaer-mascot-v3.rev` and `.riv` | Editable embedded backup and runtime export both present |
| Original native downloads | `assets/mascot/rig/v3/native/erklaerbaer_mascot_(2).rev` and `.riv` | Preserved; document-only fallback also retained, not a full artwork backup |
| Baked bear library | `assets/mascot/rig/v3/frames/`, `manifest.json`, `mascot-qa.json` | Six actions, 419 frames; all 120 neutral rim frames inspected |
| Bear review reel | `artifacts/review-v3/six-action-reel.mp4` | Corrected v3 runtime |
| Reusable artwork | `assets/library/materials/v3`, `assets/library/guitar/v3`, `assets/library/ear/v3` | Material provenance, layered SVG/PNG and recognizable ear |
| Asset browser | `assets/gallery/index.html` | Local searchable gallery; no hosted service |
| Visual evidence | `build/v3/rim-repair/`, `build/v3/mp4-qa/cedfada8807f70f3fe6b4a2c/`, `build/v3/intro-transition-qa.jpg` | Rim repair, decoded scenes and sampled transitions |
| Speech recovery | `build/audio-cache/` and episode `narration.wav` / `narration.timing.json` | Preserve to avoid paid regeneration |
| Code handoff | `deliverables/code-zips/erklaerbaer-v3-code-v003-20260909-145446.zip` | 33 entries; cumulative V3 code delta including intro, not a full project backup |
| Code file list | `deliverables/code-zips/v3-v003-files.md` | Includes narrow sibling MINT-Bot changes; restore to the named project |

Episode loudness: −15.8 LUFS, −1.4 dBFS true peak. Combined cut has the same measured levels.
Its only runtime warning is exceeding the original three-minute target by the explicitly requested intro.
70 Python tests and Ruff passed during production work. Sampled decoded visuals and checksums passed.
Full uninterrupted audiovisual review and owner creative acceptance remain open; technical validation does not grant them.

## Historical archives and recovery

- `docs/archive/2026-09-09-before-recovery-consolidation/` preserves the exact previous README, agent contract, top-level docs and review checkpoints. `index.json` maps original paths to SHA-256-verified snapshots. These files contain obsolete blockers and daily instructions; use them for history only.
- `docs/archive/OPERATIONS_pre_v3.md` preserves the older daily operating procedure.
- `artifacts/review-v2/` and earlier hashed `artifacts/review-v3/guitar/` folders are retained. The known Chirp working build is `8a24a0c4a1293ef06895d5bb`; it has older bear frames.
- Intro build `49d239b049fb17d0a0ab2b2e` is superseded: its fade mutated cached frame alpha, causing the bear to disappear on later loops. Do not reuse/upload it. Corrected build is `fb10cd42eb4001c23272e5ef`.
- Earlier code ZIPs remain intact. Use the exact `erklaerbaer-v3-code-...` prefix: older `ErklaerBaer-code-changes-...` archives are a different series, despite overlapping version numbers.
- Rive v1 master `2558769` and v2 working file `2561970` are preserved. The repaired v3 duplicate is `2564932`, named `ErklaerBaer_Mascot (2)`.
- Original private feedback remains in `feedback_andreas/`; never add it to public/asset/code packages.

No deleted data was recovered in this pass: existing local work was inventoried, stale documentation was archived, and current entry points were consolidated. No off-machine backup or Git commit was made. The largely untracked checkout and ignored media/cache files require a separate owner-controlled backup; code ZIPs and YouTube are not substitutes. See [asset recovery](ASSET_RECOVERY_V3.md).

## Remaining spending allowance

> Superseded 2026-09-13: speech and science review are now bounded per calendar month (360 Gemini requests, 750,000 characters, 200 LLM calls). The table below is the 2026-09-09 snapshot, kept for history.

Snapshot from `catalog/usage.json`; always re-read the live ledger.

| Guard | Remaining |
|---|---:|
| BFL requests | 10 |
| BFL reserved credits | 200 |
| LLM calls | 19 |
| TTS characters, including prompts | 10,571 |
| Gemini requests | 2 of 20 |
| Gemini reserved USD | $0.335872 of $3.358720 |
| Gemini trial requests | 0 of 4 |

Gemini reserved so far: $3.022848; actual billed USD is unknown. Reservations include the explicitly rejected request. Do not release them based on the lower audio-cost estimate. The intro and documentation pass made zero paid provider calls. Two remaining Gemini requests are insufficient for another complete multi-segment episode under the present guard; resolve that budget before generating coin/safari speech. No recurring allowance exists.

## How to go forward

1. **Owner:** complete the short phone-verification checklist in [SETUP.md](SETUP.md). This unlocks custom thumbnails; it does not block watching the Private video.
2. **Agent after verification:** apply the existing guitar thumbnail to video `z_1Fx6L3N_Q`, save and verify it remains Private. Do not upload a duplicate video.
3. **Agent, original implementation remainder:** finish reusable native guitar prop `.rev`/`.riv` animations on recoverable sources, export, bake and inspect the causal motion. The delivered science motion currently uses the deterministic Python compositor. Do not claim the complete native-prop objective is done.
4. **Owner:** give one consolidated audiovisual review covering intro/jingle, warmth of the bear, Dutch delivery, magnifier rim, recognizable props and scientific timing. Record acceptance only for the exact reviewed build/asset identities. Feedback on this review can guide remaining native work; it is not automatic final acceptance.
5. **After full guitar benchmark acceptance:** apply its standard to coin and safari; retain science/anatomy requirements. Check remaining provider/request caps before calls and obtain a concrete budget decision if needed.
6. **Later production:** deploy the private read-only Nochmal feed only under separate authorization, configure its dedicated read token, resolve inherited database TLS verification, extend accepted coverage to later templates and implement an unattended runner. Then perform dry-run validation. Weekly activation, public release and broader uploads require separate authorization.

Already resolved: Google API/predict access, native Rive saves, repaired runtime bake, Chrome extension file URL access, channel phone verification and YouTube API OAuth. Do not ask the owner to repeat them. `YOUTUBE_REFRESH_TOKEN` and both playlist ids are configured, so uploads run through `scripts/upload_v3_review.py` and then `scripts/finalize_v3_upload.py`. `DRY_RUN=false` must be set on the invocation; do not edit that default in `.env`.

## Local reproduction

Run from the project root with the existing Python 3.12 environment. These commands use local data and cached audio:

```bash
.venv/bin/python3 scripts/validate_v3_bundle.py artifacts/review-v3/guitar/cedfada8807f70f3fe6b4a2c
.venv/bin/python3 scripts/build_episode.py guitar --cache-only
.venv/bin/python3 scripts/build_brand_intro.py --episode artifacts/review-v3/guitar/cedfada8807f70f3fe6b4a2c --language nl-NL
.venv/bin/python3 scripts/index_v3_assets.py
```

A cache miss must fail; do not remove `--cache-only` to force success. The historical Chirp fallback was removed with the per-episode build scripts on 2026-09-13; `build_episode.py` reproduces the guitar, coin and falling-objects narration byte for byte. Rebuilding may write a new identity if dependencies change; preserve the existing review and record the new build explicitly. Do not edit sealed manifests to make changed files pass. `--language de-DE` on the intro builder changes the title-card subtitle only; it does not translate the episode.
