# ErklaerBaer production agent checkpoint

> Current review, 2026-09-09: complete 175.03-second Gemini guitar episode `cedfada8807f70f3fe6b4a2c`, repaired native v3 bear, and a reusable 12-second original synthesized intro are rendered and checked. Combined 187.03-second cut: `artifacts/review-v3/intro/fb10cd42eb4001c23272e5ef/full-review.mp4`. YouTube file access is resolved; upload `https://youtu.be/z_1Fx6L3N_Q` is saved and verified Private in the channel content list, with Dutch captions. Native guitar prop Rive assets and consolidated owner acceptance remain open. Earlier checkpoints below are historical.

Last updated: 2026-09-09, Europe/Zurich.

## Current private-review polish — 2026-09-09

The owner explicitly authorized polishing one full video and uploading it to YouTube as Private.
This supersedes the earlier upload prohibition only for this guitar review upload; public release,
weekly activation and the coin/safari gate remain unchanged. Google narrator is preferred by the
owner; bear delivery was revised to warm conversational Dutch without character acting.

Codex capacity was verified through get_usage_limits (80% five-hour remaining), resolving the
previous browser rejection. The official local runtime helper successfully baked all six actions
from the corrected native v3 runtime. All 120 neutral rim frames were inspected; contour is
continuous. Full library QA passed. Both embedded native .rev and .riv are present, with canonical
copies under assets/mascot/rig/v3. The fixed crop/pivot is preserved; corrected reel is at
artifacts/review-v3/six-action-reel.mp4. Historical working reel remains separate.

All 15 full-video speech segments are cached: 14 new calls plus one reused selected narrator
sample. The unprocessed narration was 185.0 seconds; pitch-preserving atempo=1.06 on speech only
produces 175.0205 seconds with authored prediction pauses unchanged. No audio regeneration occurs
on rerender. Full listening remains unverified by the agent. Current render identity is
cedfada8807f70f3fe6b4a2c (rendered and validated; private upload pending). All 70 Python tests and Ruff pass.

Remaining original caps: 10 BFL requests, 200 reserved credits, 19 LLM calls, 10,571 TTS characters.
Gemini reservations: 18/20 attempts, $3.022848/$3.358720; 4/4 trial attempts consumed, including the
original rejection. Actual billed USD remains unavailable. No new BFL or LLM calls in this polish.
Native reusable guitar prop Rive source/runtime is still a separate unfinished part of the original
v3 implementation; the review video uses the inspected deterministic compositor for science motion.

YouTube API auth lacks YOUTUBE_REFRESH_TOKEN. Use existing signed-in Chrome Studio tab on the
configured channel UC3yza3Tcu5vyNwr661Uai6g (@Papa_baer_andreas) for the authorized Private upload.
Do not create OAuth credentials or change account permissions. Verify final Private status.
Chrome filechooser timed out before file selection/upload. User was asked to enable Allow access
to file URLs for the ChatGPT extension; readiness is pending. The upload dialog remains open.
No file has been uploaded yet. Technical media/checksum/SRT validation and decoded 8-shot/21-
transition inspection passed; media is 175.03 s, −15.8 LUFS, −1.4 dBFS true peak.

## Earlier continuation: access resolved, browser usage blocked

Latest owner listening feedback: Gemini narrator is much better; keep that direction. Bear
still sounds artificial and needs warmer, relaxed conversational delivery. The snare-like sound
reported in the Chirp NL comparison is in a byte-identical raw TTS cache excerpt; it is not the
separately mixed guitar pluck. Precise audible cause remains undiagnosed. See the updated
`artifacts/review-v3/voices/README.md`. No new calls or code changes were made for this feedback.

The owner enabled Google API/IAM and supplied both native v3 exports. The explicit rejected-call
retry succeeded, followed by Dutch bear and German narrator samples: all three WAVs are in
`artifacts/review-v3/voices`. Listening is unverified. Reservations include the original failed
attempt; see `artifacts/review-v3/continuation-status.json` and live usage ledger for current caps.
Both `erklaerbaer_mascot_(2).riv` and embedded `.rev` exist in `assets/mascot/rig/v3/native`.
Opening the local fixed-step baker was rejected by automatic browser approval review because
Codex hit its usage limit (reported reset 09:00). No alternative browser/runtime workaround was
attempted. No fresh frame bake, full expressive narration or video rerender occurred. Existing
working video and gallery still use old v2 frames. Resume baking after access resets, then
complete native prop animation, voice assessment and full benchmark validation before review.

## Prior v3 checkpoint — incomplete creative gate

Read [V3_IMPLEMENTATION_STATUS.md](V3_IMPLEMENTATION_STATUS.md) for implemented work, exact
blockers, preserved caps and reproduction. A full 166.904-second Dutch working guitar render
exists; current assets use BFL paper/felt materials and an illustrated ear. Larger bear question
shots use a fixed visible-bounds crop. The working video still uses cached Chirp and v2 bear
frames. Do not describe it as the completed v3 benchmark or request creative acceptance yet.

Rive duplicate 2564932 is now active in desktop MCP. The narrow contour/UV repair was applied
and a native capture shows the closed rim. Pending owner actions are native runtime/embedded
backup saves (the Rive process cannot write to the project) and Google API/predict access. The first
Gemini call was rejected with SERVICE_DISABLED and remains reserved, with no automatic retry.
The rim defect is localized to the neutral contour/UV mesh; source alpha is intact. The prepared
repair preserves head bind rotation and is recorded at `build/v3/rim-repair/applied.json`.
Native capture evidence is `build/v3/rim-repair/before-after.jpg`; runtime loop inspection awaits
full exports into `assets/mascot/rig/v3/native`. A document-only recovery .rev is saved there.
The 11,524,546-byte embedded export exceeded the 8 MiB inline limit after macOS denied disk access;
do not retry that known fallback or cloud upload. Use the native Export/Save dialog.

Implemented: typed v3 shots/speaker profiles; finite Gemini token/USD reservations and explicit
rejected-call recovery; layered guitar/ear materials and local asset gallery; exact rendered
build/audio/timing validation; private locked weekly selector and local MINT read-only endpoint.
The MINT edits are limited to the new endpoint and read-token rejection in `lib/db.js`; existing
owner edits to notify scripts/workflow remain untouched. No DB query, deployment or activation.

Offline Python suite: 70 tests passed at this checkpoint. Node mocked feed harness passes with
83 records and verifies auth/method isolation. Ruff passed at handoff. The
current guitar text independently passed science/language review; creative and listening status
remain separate. Preserve all historical output, feedback and the largely untracked checkout.

Latest verified working build: `8a24a0c4a1293ef06895d5bb`. The exact-build validator passed;
media measured 1920×1080/30 fps, 166.9 seconds, −16.8 LUFS and −1.3 dBFS true peak. Sampled
decoded frames cover all eight shots and seven transitions, with selected full-resolution checks.
Bear-free scene durations total 80.79% of runtime. This is sampled inspection, not full playback
or listening. Evidence and open corrections are in `artifacts/review-v3/validation.json` and
`artifacts/review-v3/feedback-to-fix.md`. Cache reuse returned the same render with an unchanged
usage ledger. No paid calls were made during the final verification continuation. The latest desktop MCP check targets v3 2564932; the recorded contour edit has been applied.

Code-only archive: `deliverables/code-zips/erklaerbaer-v3-code-v001-20260909-041150.zip`;
included paths are in `deliverables/code-zips/v3-changed-files.md`. It contains the explicit v3
code delta and narrow MINT edits, excludes assets/private data, and passed a configured-secret scan.

Lessons: native editor and browser tabs are distinct Rive sessions; creating/opening a browser
duplicate does not switch desktop MCP. Inspect source-versus-bind-versus-bake before editing a
rim defect. Google Cloud TTS availability does not imply Gemini's aiplatform API is enabled.
A 403 is not a successful voice sample; retain the reservation and explicit failure evidence.

Tools: official loopback Rive MCP read-only mesh/UV/bind capture; Chrome UI for recoverable file
duplication; bounded BFL EU artwork and Anthropic public-script review; Google TTS/Service Usage
checks; Pillow/ImageIO fixed-timing MP4 render and decoded-frame inspection; local HTML gallery
browser search check; Pytest/Ruff and mocked Node endpoint tests. No subagents were spawned.

Owner feedback on 2026-09-09: overall design is much better, but the magnifier is still broken
in the working MP4. This is positive direction, not consolidated creative acceptance. Existing
MP4/reel frames remain historical v2 until a fresh corrected runtime is exported and baked.

## Historical v2 checkpoint and approved planning record

# ErklaerBaer production agent checkpoint

Last updated: 2026-09-08, Europe/Zurich

## Approved v3 continuation

The owner approved the redesign plan and prompt saving. Active instructions are
[PRODUCTION_V3_PROMPT.md](PRODUCTION_V3_PROMPT.md) and [V3_REDESIGN_PLAN.md](V3_REDESIGN_PLAN.md).
The private feedback folder is now gitignored. V2 technical validation remains valid as historical
evidence, but visual quality and narration require revision; no creative approval was granted.

Next work: Dutch guitar benchmark in paper/felt collage, repair the magnifier rim, size the bear
from visible bounds, trial expressive Google narration/bear voices, and build reusable asset indexing.
Prepare the read-only Nochmal feed and weekly queue without deployment. Keep the existing remaining
caps. After the complete benchmark, obtain creative review before wider production.

New lessons: technical media/alpha tests do not prove object recognition, scientific readability,
or narration quality. Transparent canvas biases bear sizing; the current gas trajectories reflect
inside an inset rectangle rather than the drawn wall. The MINT schedule does not contain private
Nochmal state, and the existing state endpoint returns unnecessary family history. These findings
are explicitly addressed in the v3 prompt. Tools for this review: OOXML extraction plus embedded-image
inspection, local source searches, official provider/model documentation, and Git ignore checks.

The detailed v2 record below is retained as history, not the current completion claim or next-step list.

This is the durable working checkpoint for the implementation authorized by
`docs/PRODUCTION_PROMPT.md`. It records observed state rather than replacing that prompt. Continue
autonomously within its scope and spending caps. Do not upload, publish, activate production,
commit, push, or treat silence as creative approval.

## Current outcome

The approved Rive v1 master remains unchanged at file ID `2558769`. All authoring writes were made
to the recoverable duplicate `ErklaerBaer_Mascot (1)`, file ID `2561970`. The duplicate now contains
six semantic actions:

| Action | Rive animation | Duration | Playback | State value |
|---|---|---:|---|---:|
| Neutral | `idle_loop` | 4.0 s | loop | 0 |
| Lift | `lift_v2` | 2.0 s | play once, hold | 1 |
| Explain | `explain_v2` | 2.0 s | play once, hold | 2 |
| Think | `think_v2` | 2.5 s | play once, hold | 3 |
| Surprise | `surprise_v2` | 1.5 s | play once, settle | 4 |
| Aha | `aha_v2` | 1.8 s | play once, settle | 5 |

The state machine keeps its real contract name, `State Machine 1`. A new numeric view-model property
`ViewModel1.action` controls the six values above. The inherited state machine had an unconditional
Any State to Lift transition. That transition is now conditional, the old Neutral/Lift/Explain
conditions use the new view-model property, and Think/Surprise/Aha states and conditions were added.
Simulation selected the expected final state for all values 0 through 5. The legacy Neutral image
key was moved from frame 1 to frame 0. The accepted head bind rotation remains
`-0.10641551025538434` degrees.

Think, Surprise, and Aha were generated once each from the approved neutral reference through the
pinned EU FLUX.2 Pro endpoint. Their RGBA inputs were imported, meshed, bound to the three existing
bones, and auto-weighted. No candidate revision was needed. The pose images remain provisional.
Lift uses the accepted artwork with a stone already in the pose; production scenes must coordinate
that held pose with a separate scene prop and must not show a fake second stone.

The Rive runtime and full embedded backup exports are now secured in the project. The first browser
download produced an 11,731,889-byte runtime, SHA-256
`ab628b6f569e5a70b8351c6d44d70d372c4503f363c0e62929371a3fd08a370d`. A real runtime bake proved
that it contained only `idle_loop`: `ViewModel1.action` and all non-default timelines had been
removed by Full optimization because the view-model instance was not bound to the artboard. The
live duplicate is now repaired: `ViewModel1` / `Instance` is bound to artboard `0-2`.

The corrected native runtime is now `assets/mascot/rig/v2/erklaerbaer-mascot-v2.riv`, 11,743,468
bytes, SHA-256 `0e291bb163dc8a9e713a4fd04fe306457f795af501dc4163e3809c71441e0c75`.
The full embedded backup is `assets/mascot/rig/v2/erklaerbaer-mascot-v2.rev`, 11,523,132 bytes,
SHA-256 `6cac4e9f47f18e32d4f3abc564b7f992872c0ea71a81085c4ce17f743d375196`.
The rejected runtime remains at
`assets/mascot/rig/v2/erklaerbaer-mascot-v2-unbound.rejected.riv` for audit purposes.

The earlier fallback successfully produced a 62,434-byte document-only backup at
`assets/mascot/rig/v2/erklaerbaer-mascot-v2-document-only.rev`, SHA-256
`61201139d713011b7ca78c12b7023ee8f300307eda2219999af158e0b356198d`. It omits embedded raster
assets and therefore does not replace the full native backup. A second document-only export after
the binding repair was byte-identical, which confirms deterministic document export. Uploading
either revision as a fresh cloud duplicate was rejected by Rive's server. Do not repeat large inline
or cloud-upload attempts.

The corrected runtime exposed all six timeline names and baked 419 transparent frames at 600x800
and 30 fps. `assets/mascot/rig/v2/mascot-qa.json` passes checksums, dimensions, mixed alpha, minimum
coverage, safe bounds, Neutral loop continuity, one-shot motion, and action distinctness. The global
bounds are `[86, 125, 520, 714]`; the Neutral loop-seam mean error is `0.0027`; non-Neutral starts
differ from Neutral by `16.47` to `20.50` mean pixel units. The rebuilt labelled review reel is
`artifacts/review-v2/six-action-reel.mp4`, SHA-256
`0140fddc2c5cd64a6d577f85132bb2769ff584795403a7e0a7bcd59670736493`.

## Science and narration state

The three MINT snapshots are preserved locally with their original 16-character hashes:

- `springende-muenze`, de-DE: `0d6d2f1d3eb3b75d`
- `karton-gitarre`, nl-NL: `7511ac9042e30f1e`
- `krabbeltier-safari`, nl-NL: `3b0beaeef4efbdf8`

Compact evidence packs were added under `docs/evidence/`. They cite OpenStax, UNSW guitar acoustics,
the Smithsonian, and The Wildlife Trusts. The corrected local v2 storyboards are in the canonical
`storyboards/` paths and use explicit speech segments, mechanism objects, relationships, and ordered
beats. They remain separate from upstream MINT. Principal corrections:

- Coin: gas is mostly empty space; the rigid bottle stays approximately fixed in volume; heating
  raises mean particle speed and pressure; lift, venting, pressure reduction, and reset are distinct.
- Guitar: vibration is transferred from string to box to locally oscillating air; the box does not
  create energy; pitch follows frequency; no unsupported thickness or box-size rule is asserted.
- Animals: adult insects have 6 legs, spiders 8, and adult woodlice 14; not every small animal is an
  insect or detritivore; not every woodlouse rolls into a ball; no universal under-every-stone claim.

An independent Anthropic science/language pass approved all three current scripts. Each approval is
content-addressed in `docs/evidence/reviews/` and copied to `<topic>.review.json`; changing the script
or evidence invalidates it. This is not owner creative approval and does not approve visual output.

The coin narration was synthesized twice because the first measured speech was too fast. Speaking
rates are language-specific: German is `0.85` and Dutch is `0.72`. The retained current coin
narration is 139.842 seconds with 19 measured segments, 127.5 spoken words per minute and 118.4
words per minute including pauses. Its first 0.98-rate version remains in the content-addressed
cache. Do not delete it. Final guitar narration is 166.904 seconds with 15 measured segments and
114.9 spoken words per minute. Final animal narration is 176.613 seconds with 15 measured segments
and 107.5 spoken words per minute. Earlier Dutch 0.85 and 0.71 identities remain cached and must not
be deleted. All three final SRTs exist in their local review directories.

All three fingerprinted production pilots are now rendered and copied into
`artifacts/review-v2/pilots/` with captions, thumbnails, timing JSON, reviewed storyboards, and
science-timing proofs. Their current build hashes are:

- `springende-muenze` / de-DE: `4e0c3cb535e39d89a3235e32`
- `karton-gitarre` / nl-NL: `d4ff8a1fe55d79e548550733`
- `krabbeltier-safari` / nl-NL: `729348c4fb407962e7175fdf`

The strict package report is `artifacts/review-v2/validation.json` and passes without warnings.
Runtimes are 139.83, 166.90, and 176.60 seconds; all are 1920x1080 H.264 at 30 fps with mono AAC
at 48 kHz. Integrated loudness is -16.4, -16.8, and -16.9 LUFS; true peaks are -1.4, -1.4, and
-1.3 dBFS. Captions contain 19, 15, and 15 non-overlapping intervals within their videos.

## Code implemented

- `src/erklaerbaer/budgets.py`: persistent production-v2 allowance, atomic lock, monthly preservation,
  separate actual-charge records.
- `src/erklaerbaer/asset_design.py`: new pose whitelist/prompts, approved neutral reference, conservative
  reservation, recoverable request journals, EU endpoint.
- `src/erklaerbaer/models.py`: six actions, explicit mascot shots, speech segments, whitelisted mechanism
  schemas and beat validation, build hashes.
- `src/erklaerbaer/speech_cache.py` and `audio.py`: content-addressed segment PCM cache, pending-submission
  gate, persisted measured timings, segment-only regeneration, cache-only visual rerenders.
- `src/erklaerbaer/captions.py`: subtitles aligned to measured segment intervals.
- `src/erklaerbaer/build_identity.py`, `paths.py`, `catalog.py`, and `pipeline.py`: content fingerprint,
  versioned artifacts, immutable uploaded versions, approval isolation, and science-review validation.
- `src/erklaerbaer/mechanisms.py`: deterministic gas-pressure, vibrating-string, and animal-observation
  drawings driven by real narration segment starts.
- `src/erklaerbaer/mascot_library.py` and `renderer.py`: transparent clip integration, global neutral-loop
  clock, clamped one-shots, explicit visibility/placement, and science views using at least 70% of
  usable width when the mascot is present. The old procedural renderer remains only for schema-v1
  compatibility; v2 fails if its explicit mechanism/timing data is absent.
- `scripts/rive_mcp.py`: loopback-only official Rive MCP client. It never prints inline export bytes.
- `scripts/author_rive_v2.py`: one-time duplicate authoring recipe; do not rerun blindly because it is
  not fully idempotent after successful keyframe insertion.
- `scripts/rive-bake/`: isolated official `@rive-app/canvas-advanced` 2.42.0 runtime and localhost bake
  bridge. It accepts only the expected Rive file and token-authenticated 600x800 RGBA PNG frames.
- `scripts/prepare_pilots.py`, `review_pilots.py`, `narrate_pilot.py`, and `preview_mechanisms.py`:
  reproducible local production helpers.

Mechanism contact sheets currently live in `build/production-v2-review/`. Visual inspection found
the overall causal layout readable. Follow-up corrections already made include stable bottle aspect,
plain slash separators instead of missing-font middle-dot glyphs, and slimmer animal bodies so all
legs remain visible. Regenerate and re-inspect the sheets after the current formatter pass.

## Spend and persistent caps

The allowance is one task-wide pool and does not renew on resume or month changes. Current ledger
state from `catalog/usage.json`:

| Resource | Additional used/reserved | Additional cap | Remaining |
|---|---:|---:|---:|
| BFL reserved credits | 60 | 300 | 240 |
| BFL requests | 3 | 15 | 12 |
| LLM calls | 4 | 24 | 20 |
| TTS characters | 12,552 | 30,000 | 17,448 |

Actual BFL charge recorded: 22.5 credits total, 7.5 for each accepted pose. Historical monthly
baseline before this task was 100 BFL reserved credits, 78 LLM calls, and 11,299 TTS characters.
Current September totals are therefore 160, 82, and 23,851 respectively. No top-up or purchase was
made. The retained cache contains deliberately superseded pacing identities: two coin runs, three
guitar runs, and two animal runs. The final settings select only the current language-rate identity.

## Tools used and how

- Shell/Python: inspected the untracked checkout with `rg`, read JSON/TOML, ran the project CLI,
  generated deterministic assets, and ran Pytest/Ruff. Python commands always use `python3` or the
  Python 3.12 virtual environment.
- Official Rive MCP at `http://127.0.0.1:9791/mcp`: initialized the protocol, queried hierarchy,
  properties, timelines, meshes, state machines and view models; captured transparent previews;
  uploaded RGBA assets via base64 fallback; authored meshes, keyframes, states and conditions; ran
  state-machine simulations; attempted supported exports. Connection remained loopback-only.
- Computer Use in Chrome: verified the Cadet account, duplicated the approved cloud file, opened the
  duplicate, used the normal export/download UI, and preserved the live editor tab. Do not use
  shell-based browser automation. Automatic review refused navigation away from the authored editor
  because unsaved work might be lost, so a separate Personal Files tab was used. Browser security
  policy also blocked `chrome://downloads`; it was not bypassed.
- BFL API: three authorized scoped calls to the pinned EU FLUX.2 Pro endpoint, one candidate per new
  expression. Request journals contain polling URLs and must not be printed or included in delivery.
- Anthropic API: four bounded public-data review calls so far. Three were the initial pilot reviews;
  the coin script changed to expose lift/vent/reset as separate beats, so only that script was
  re-reviewed. No confidential or unrelated project data was sent.
- Google Cloud TTS: two bounded calls for the two content-distinct voice identities of the coin
  narration. Segment audio and durations are local and content-addressed. No unrelated data was sent.
- Web research: read only authoritative public pages for science and official Rive/BFL documentation.
- Image inspection: viewed transparent Rive captures and composite/contact-sheet PNG/JPEG outputs.
- Bundled ImageIO FFmpeg: encoded the labelled action reel and production previews, then decoded
  representative frames for contact-sheet inspection. This avoids relying on a system FFmpeg install.

Connected model use may expose selected artwork and tool results to that model provider's context.
No client, financial, credential, or unrelated child-project data was transmitted. `.request.json`
files are operational journals and must stay out of archives and commits.

## Lessons learned

- Written Rive documentation is a starting point, not proof of editor behavior. Query the live file,
  inspect authored objects, and simulate every public action value before accepting the rig contract.
- State-machine transitions can exist without effective conditions. The inherited Any State transition
  silently selected Lift until its condition was repaired; enumeration alone would not have found it.
- The Early Access app separates its native export sandbox from browser download behavior. Direct MCP
  project paths were denied, browser cloud downloads lagged the in-memory revision, and inline export
  has an 8 MiB ceiling. The app can write its own private container, but macOS blocks Codex from reading
  back out of it. Preserve the document-only recovery export, but require native saves of the full
  `.riv` and embedded `.rev` into the project.
- Speech speed cannot be inferred reliably from the nominal API rate across languages and voices.
  Measure the generated audio, compute spoken and overall words per minute separately, and retain prior
  content-addressed identities so pacing corrections remain auditable.
- Visual beats must use measured segment starts. Guessing word-level timing causes mechanism changes to
  drift away from the narration even when the total video duration is correct.
- A reproducible build identity must include every content and asset input that changes pixels or sound,
  while excluding review status, timestamps, machine paths, and approval bookkeeping.
- Rive editor simulation is insufficient runtime proof. A production export must enumerate and decode
  every named action. Binding the view-model instance to the artboard is what keeps conditionally
  reachable timelines alive under Full optimization.
- Paid-call safety needs reservations and recoverable request journals. This is deliberately conservative:
  an interrupted request may temporarily consume allowance even when the provider later reports a lower
  actual charge, but it prevents an uncertain retry from duplicating spend.

## Verification completed

- Rive reversible root-position edit was made, captured, and restored.
- State-machine simulations passed for action values 0 through 5.
- Three new RGBA assets were inspected; no extra limbs, ears, text, or obvious scarf/identity defect.
- The corrected runtime baked 419 frames across all six actions. Automated alpha, bounds, checksum,
  loop, motion, and distinctness checks pass, and a reel contact sheet was inspected.
- Three evidence-grounded storyboards passed content-addressed independent review.
- Renderer mechanism contact sheets and representative frames from all three full MP4s were inspected
  after refinement. The bear does not occlude the causal diagrams, and the held-stone Lift pose is not
  used beside a second lifted prop.
- After formatting and a legacy-release compatibility repair, the production package passes Ruff and
  the offline suite reports 62 passing tests. A full-repository Ruff scan separately reports ten
  historical issues in the retained root-level `create_video.py`; production-v2 does not import it.

## Next steps, in order

1. Obtain one consolidated owner creative sign-off on the exact library and three pilots. Review the
   held-stone Lift limitation and the German/Dutch pronunciation, pacing, child engagement, and visual
   fit. Keep every asset/build provisional until explicit approval.
2. Upload or publish only after a separate explicit authorization. No upload, public sharing, Git
   commit, or push is part of the current authorization.

The checkout is almost entirely untracked. Do not bulk-stage, discard, reset, or overwrite owner work.
