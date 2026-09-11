# V3 guitar implementation checkpoint

> Current review, 2026-09-09: complete 175.03-second Gemini guitar episode `cedfada8807f70f3fe6b4a2c`, repaired native v3 bear, and a reusable 12-second original synthesized intro are rendered and checked. Combined 187.03-second cut: `artifacts/review-v3/intro/fb10cd42eb4001c23272e5ef/full-review.mp4`. YouTube file access is resolved; upload `https://youtu.be/z_1Fx6L3N_Q` is saved and verified Private in the channel content list, with Dutch captions. Native guitar prop Rive assets and consolidated owner acceptance remain open. Earlier checkpoints below are historical.

> Latest 2026-09-09 polish: the repaired native bear has been exported and all six actions baked
> and checked, including the complete neutral rim loop. Full Gemini narration is generated with
> warmer bear delivery; a 175.0205-second private-review video is being rendered. The owner now
> explicitly authorizes this one YouTube Private upload. See AGENT_STATUS.md for current work and
> costs; the access-blocker and spending sections below describe the earlier checkpoint.
> Native reusable guitar prop .rev/.riv remains unfinished; this review uses deterministic science
> animation. Full benchmark implementation and consolidated owner acceptance are still distinct.

Status: implementation in progress; the first creative gate is **not complete**.
Updated 2026-09-09. The active authority is [PRODUCTION_V3_PROMPT.md](PRODUCTION_V3_PROMPT.md).

## Available local work

A complete 166.904-second Dutch guitar working video has been rendered at 1920×1080/30 fps,
with captions, thumbnail, measured audio timings, checksums and a sealed build identity under
`artifacts/review-v3/guitar/<build-hash>/`. The latest current build is identified in
`artifacts/review-v3/validation.json` after validation. Earlier hashes remain historical snapshots.
The current verified hash is `8a24a0c4a1293ef06895d5bb`. Technical validation passed, and sampled
decoded frames cover eight shots and seven transitions. See
[`feedback-to-fix.md`](../artifacts/review-v3/feedback-to-fix.md) for observations and open work.

The paper/felt redesign uses BFL material artwork, exact editable box/support geometry, an
illustrated outer ear, fixed string attachment points, displacement/release, magnified surface
motion, a finite-speed pressure pattern, particles oscillating about fixed equilibrium locations,
and a decaying oscillation. A restrained synthesized 220 Hz pluck is placed after the narration
that explains slowed motion. This is an illustrative sound, not a recording of the depicted box.

Question/reaction shots use a substantially larger bear with one fixed library crop and ground
pivot. The bear is absent from all six dedicated explanation/recap shots. The current bear
frames remain v2 exports, explicitly labelled as awaiting the native v3 repair.

The v3 storyboard is separate at `storyboards/v3/karton-gitarre/nl-NL/7511ac9042e30f1e.json`.
It adds validated template/version, shot framing, semantic coupling/surface/propagation/hearing
cues, and speaker/delivery roles. The independent public science/language review passed and is
stored separately under `docs/evidence/v3/`; historical v2 reviews remain valid and unchanged.

## Blocking account/editor actions

1. The v3 duplicate **ErklaerBaer_Mascot (2)**, file **2564932**, is now active in desktop Rive.
   The contour/UV correction has been applied and the native capture shows a closed rim.
   Export **For Runtime (.riv)** and **For Backup (.rev, embedded assets)** using the native
   Save dialog into `assets/mascot/rig/v3/native`. The MCP process was denied filesystem access;
   the embedded export is 11,524,546 bytes, above its 8 MiB inline fallback. A small document-only
   recovery backup was saved, but cannot replace the full native exports or runtime verification.
   No v1/v2 authoring writes were made. The existing working video still uses old v2 frames.
2. Enable `aiplatform.googleapis.com` in the existing Google project and ensure the existing TTS
   service account has `aiplatform.endpoints.predict`. The first Gemini sample returned explicit
   HTTP 403 `SERVICE_DISABLED`; a later read-only Service Usage status request was also denied.
   No audio was returned. No API enablement, IAM expansion or account purchase was performed.
   Never paste credentials into chat. After the owner confirms the service is ready, use the
   explicit rejected-request recovery command below; do not remove journals by hand.

The original/cleaned alpha retains the complete magnifier rim. A coarse neutral mesh cuts an
inward notch into its upper-left arc; the notch is present in the native bind capture and the
baked frame. Evidence is at `build/v3/rim-evidence.jpg`, with queried mesh/UV properties beside it.
`repair_rive_v3_rim.py` stages a narrow contour/UV correction on vertices `0-120` and `0-225`,
refuses any file except 2564932, preserves the head bind rotation, and records before values.
**Applied on 2026-09-09; native still inspected.** Before/after capture evidence is in
`build/v3/rim-repair/before-after.jpg`. Full native exports and a fresh six-action bake remain
required to validate the animated rim. The current working reel still uses the old frames.

## Remaining acceptance work

- Save the repaired native embedded `.rev` and `.riv`, bake all six semantic actions with the
  official helper, and inspect the entire neutral loop. Native still inspection passed.
- Author/bake reusable layered guitar prop animations in Rive. Current guitar science motion is
  deterministic compositor code; editable layered SVG/PNG exists, but prop `.rev`/`.riv` does not.
- Finish short German/Dutch Gemini-versus-Chirp samples and a distinct bear voice, listen, select,
  and synthesize the benchmark within the retained caps. Current full video uses cached Chirp.
- Inspect final full-resolution MP4 transitions, surface/air coupling, timing and narration after
  native/voice changes. Current still and decoded working-video frames were inspected; listening
  and final creative fit remain unverified.
- Complete source/runtime bundles and the final measured cost/quality package. Only then request
  consolidated owner creative review. Coin and safari remain behind this gate.

## Persistent spending

The ledger remains `catalog/usage.json`, with the original `production_v2` task pool preserved.
V3 work so far: two BFL requests (material sheet and ear), 40 credits reserved, 12 actual credits;
one LLM science review; one rejected Gemini request reserving 393 characters including instructions.
Remaining: **10 BFL requests, 200 reserved credits, 19 LLM calls, 17,055 TTS characters**.
Total actual BFL charges across v2 and v3 are 34.5 credits; reservations are not refunds or charges.

Gemini is additionally bounded to 20 request attempts, at most 4 trial attempts, and
**$3.358720 reserved total** for this one trial/benchmark implementation. Each request reserves
8,192 input tokens and 16,384 audio tokens, or **$0.167936**, using documented model maxima.
One rejected attempt remains reserved; no counters were refunded. The remaining three trial
attempts cover Dutch narrator, Dutch bear, and German narrator. German bear consistency is not
claimed. These are finite local guards, not a new recurring allowance.

Pricing checked 2026-09-08: [Google pricing](https://cloud.google.com/text-to-speech/pricing)
quotes $0.50/M input tokens and $10/M audio tokens for Gemini 2.5 Flash TTS, with 25 audio tokens
per second. [The model/API limits](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts)
specify 8,192 input/16,384 output tokens and 4,000 bytes per text/prompt field. No actual token
usage/billed dollars is returned by this synthesis interface: measured duration-based estimates,
input upper bounds, and provider-reported actual charges are distinct fields. Never call an
estimate an invoice. No new dependency, provider, top-up, subscription or purchase was introduced.

## Reproduce locally

```bash
# No TTS/writer calls; the complete working render reuses cached Chirp segments.
.venv/bin/python3 scripts/build_v3_guitar.py
.venv/bin/python3 scripts/preview_v3_guitar.py
.venv/bin/python3 scripts/index_v3_assets.py
.venv/bin/python3 scripts/validate_v3_bundle.py artifacts/review-v3/guitar/BUILD_HASH

# Only after the owner has activated the v3 duplicate in desktop Rive:
.venv/bin/python3 scripts/repair_rive_v3_rim.py
# Export the full native files, then use the existing official fixed-step helper:
.venv/bin/python3 scripts/rive-bake/serve.py --riv assets/mascot/rig/v3/erklaerbaer-mascot-v3.riv --library assets/mascot/rig/v3
.venv/bin/python3 scripts/build_mascot_reel.py --library assets/mascot/rig/v3 --output artifacts/review-v3/six-action-reel.mp4

# Only after Google service/IAM readiness is confirmed; preserves the rejected reservation:
DRY_RUN=false .venv/bin/python3 scripts/trial_v3_voices.py --retry-rejected
# After listening to the trial:
DRY_RUN=false .venv/bin/python3 scripts/build_v3_guitar.py --expressive
.venv/bin/python3 scripts/build_v3_guitar.py --expressive --cache-only
```

The review validator recomputes the current dependencies and exact audio/timing identity and
rejects stale or tampered bundles. Approval bookkeeping does not change the fingerprint. The v2
packager now rejects old renders whose current dependencies differ; retained historical v2
packages are evidence of that historical build, not current approval.
