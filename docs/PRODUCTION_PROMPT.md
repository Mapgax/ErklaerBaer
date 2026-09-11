# ErklaerBaer autonomous production continuation

> For current delivery, subsequent owner authorizations, archives and remaining work, see [Recovery and next steps](RECOVERY_AND_NEXT_STEPS.md). The original requirements/history below remain preserved.



Historical v2 prompt. The owner-approved [v3 implementation prompt](PRODUCTION_V3_PROMPT.md)
supersedes conflicting scope, cadence and creative-review instructions. Preserve the task ledger;
v3 does not grant a fresh allowance. V2 technical completion did not establish creative acceptance.

Copy the prompt below into the implementation task. It authorizes execution, not just planning.
Its bounded authorization belongs to this upgrade and does not renew on each resume.

---

Implement the ErklaerBaer production upgrade in:

`/Users/andreas/Projects/AI/ErklaerBaer`

Approved Rive v1 master: <https://editor.rive.app/file/erklaerbaer_mascot/2558769>

Read `docs/SPEC.md`, `docs/SETUP.md`, `docs/RIVE_RIG.md`,
`assets/mascot/rig/REVIEW.md`, `assets/mascot/rig/rig-contract.json`, and applicable `AGENTS.md`
instructions. If no repository `AGENTS.md` exists, use the owner instructions in this task/session;
do not block on the absent filename. Inspect existing code, media, assets and Git status first.
The SPEC's v2 scope and this prompt supersede historical per-step v1 gates and the three-pose-only
restriction. Preserve historical reviews. The owner is arranging one month of Cadet; verify export
entitlement rather than assuming it is active.

## Objective, authorization and spending

Deliver a reusable six-action bear library and three complete local science videos without the
owner editing Rive or assembling scenes. Implement, verify, repair and render autonomously.
The owner's role is reviewing finished building blocks and videos.

Authorized: project code/docs/configuration changes; local assets/media; a scoped official Rive
MCP connection where host permissions allow; editing a duplicate of the approved Rive file;
bounded calls using existing BFL, Anthropic and Google TTS credentials; and read-only authoritative
science/provider research. These external calls and Rive writes do not need per-step confirmation.

Task caps shared across retries, resumes and month boundaries: 300 additional BFL reserved credits
(USD 3), at most 15 BFL requests including revisions, 24 additional LLM calls and 30,000 additional
TTS characters. Respect available prepaid funds, provider limits and existing monthly LLM/TTS
ceilings. The original 100 BFL reserved credits are already used. Implement a persistent task
allowance and reconcile the old monthly BFL ceiling without resetting/deleting counters. Reserve
a conservative model/input/output cost bound before each call; keep the existing 20-credit reserve
only while adequate. Record actual charges separately. Recover uncertain submissions before
retrying to avoid double charges. No purchases, automatic top-up, paid Rive AI credits, new paid
providers or automatic increases to the task caps.

Keep default dry-run behavior; use scoped live invocations for authorized local work. YouTube/OAuth
setup is not required to generate artwork or render locally. No YouTube upload, playlist write,
public sharing, upstream MINT change, Git push or production activation is authorized. Never print
credentials or transmit unrelated project/child data.

## 1. Verify the baseline and connect Rive

Inspect known findings: the renderer still uses the procedural bear; production Rive exports are
missing; a test expects `MascotController` while the approved contract says `State Machine 1`;
visual rerenders synthesize TTS again; source-only identity misses asset changes; much of the
checkout is untracked. Resolve the actual causes without discarding owner work.

Discover and use official Rive MCP tools. Consult <https://rive.app/docs/editor/ai/mcp>; its
documented desktop endpoint is `http://127.0.0.1:9791/mcp`. Verify availability and supported
methods on the latest supported desktop/Early Access editor. Configure the scoped connection if
possible; do not install an unofficial community MCP server. Keep it on loopback. Explain briefly
that selected artwork and scene/tool results may enter the connected model provider's context.

Inspect the artboard, assets, hierarchy and timelines. Create a recoverable duplicate; obtain a
`.rev` backup when available. Prove MCP with a small reversible property/keyframe edit and inspect
its result. Preserve the v1 master, bind-pose values and aligned eyelids. Reconcile actual contract
names and tests; do not rename the rig just to satisfy a stale test. Documentation is not proof
that mesh editing, visual capture or export works through the connected tools.

If login, installation/launch, entitlement or an enforced permission boundary requires the owner,
ask for that exact action and continue independent work. Do not claim untested access or replace
automation with repeated instructions for the owner to manipulate timelines.

## 2. Generate and animate the missing expressions

Preserve Neutral, Lift and Explain, the approved felt/paper texture, proportions, teal scarf and
accepted cleanup. Add Think/Curious, Surprise and Aha/Understood. Use the approved neutral bear
as the canonical BFL reference and accepted poses where useful. Use the configured pinned FLUX.2
EU endpoint unless official evidence requires a documented compatible change. Extend the local
generator's pose whitelist/metadata as needed. This is an occasional asset pass, never daily work.

Generate one candidate at a time, inspect it and revise only when necessary within the cap. Reject
identity drift, extra limbs/ears, awkward scarves, obscured eyes, text and false scientific details.
Prepare clean RGBA assets; inspect light/dark/teal composites and enclosed gaps. Retain rejected
candidates and reasons separately. Do not pause for owner approval of each still before animation.

Use official MCP to author and inspect:

- Neutral: accepted restrained idle, subtle neutral head deformation and synchronized blink.
- Explain: small deliberate indicating gesture and quiet hold.
- Lift/reveal: short action coordinated with a separate scene prop. Separate/correct a baked-in
  stone or document a held-pose limitation; moving a second stone is not a valid lift animation.
- Think: brief tilt followed by a quiet attentive prediction hold.
- Surprise: changed facial expression, quick restrained reaction, short hold and settle.
- Aha: understood/satisfied expression, small nod or raised paw and settle.

Surprise and Aha initially last about 1–2 seconds and play once. Do not implement every state as
an idle loop or stretch clip timing to narration length. Small head/arm movements needed for the
six actions and new face artwork/minimal layers are authorized. No lip-sync, independent gaze
system, walking cycle, wholesale rebuild or large deformations of flattened artwork. Resolve
technical corrections independently and inspect actual motion at intended video size.

## 3. Export and integrate the local library

Export `.rev` and `.riv` plus all six actions at 30 fps. Preserve v1; use versioned v2 directories.
Update the contract with actual filenames/names, semantic action mappings and observed capabilities.
Distinguish proposed, implemented, technically checked and owner-approved states.

Prefer WebM only if decoded alpha and visible edges pass in the actual production decoder;
otherwise use RGBA PNG sequences. Validate loop seams, first/last frames, one-shot completion,
transitions, consistent anchors and bounds. Save checksums and a manifest containing dimensions,
FPS, duration, pivots, loop/hold/settle behavior, filenames and provisional review status.

Use supported Rive export first. If unsuitable, a small isolated official runtime helper may bake
local `.riv` files to transparent frames at fixed timesteps. A Node/JS helper is allowed only with
a documented reason and dependency/license/maintenance check. Do not add a live daily Rive
dependency or rewrite the renderer. If automated export is inaccessible, prepare everything
possible before requesting the smallest necessary owner action.

Integrate clips into the existing Pillow/NumPy/imageio-ffmpeg renderer. Add explicit mascot
visibility, placement, semantic action and timing to the validated storyboard. Generated data
must never execute arbitrary code. Provisional assets are allowed in local review renders only;
upload/release must reject them until the owner accepts those exact asset versions.

## 4. Make the science visible and synchronize it

Support full-frame science views and small-mascot shots. Start with at least 70% of usable width
for science in shared shots, and the bear absent during at least half of explanatory runtime;
tune these design defaults from actual results. Use the bear for questions, predictions and short
reactions. Keep it still or absent during detailed mechanisms. Remove the permanent mascot column.

Build reviewed reusable mechanisms with explicit objects/relationships and ordered actions.
Derive phrase/beat timing from actual narration segments or supported verified timepoints, not
guessed word alignment. Cache audio by text/markup, language, voice, provider and audio settings;
persist segment durations. Visual-only rerenders must use identical cached audio with no TTS or
writer call. Regenerate only missing/changed segments. Preserve natural speech, a deliberate
prediction pause and captions aligned to speech rather than silent padding.

Create compact local fact packs with authoritative citations. Correct/revalidate old storyboards;
an old `approved: true` is not proof. Review actual rendered mechanisms against evidence. For the
coin: heating, faster gas motion/collisions, pressure increase at approximately fixed volume,
coin lift, escaping air and reset. Remove tightly-packed-gas wording and the implication that
the rigid bottle expands. Preserve the MINT snapshot/hash and record supported corrections
locally. Do not edit upstream MINT; unresolved material uncertainty needs owner input.

Add a deterministic build fingerprint covering storyboard/evidence, renderer revision, mascot
asset hashes and voice/timing settings. Migrate catalog/artifact/release handling safely. Preserve
uploaded versions, invalidate stale local renders and require new approval for changed builds.
Exclude timestamps, machine-specific absolute paths and mutable approval status from the content
fingerprint; approving an artifact must not create another unapproved version.

## 5. Render, verify and deliver

Produce complete local pilots in order:

1. `springende-muenze` / `de-DE`: visible causal mechanism.
2. `karton-gitarre` / `nl-NL`: string vibration and sound.
3. `krabbeltier-safari` / `nl-NL`: reveal, observation and anatomical comparison.

Inspect and repair the first, then reuse the system for the next two without owner timeline
adjustments. Do not stop at a still, contact sheet or teaser. Reuse valid cached work and perform
bounded regeneration where script/scientific changes require it.

Run the existing suite and meaningful checks for decoded alpha/edges, loops/one-shots, semantic
action selection, timing/captions, safe margins/occlusion, fixed-seed frames, build invalidation,
approval isolation and zero paid calls for visual rerenders. Inspect actual MP4 frames/transitions
and narration where tools permit; disclose anything unverified. Check codecs, duration, loudness
and both languages' pronunciation/pacing. Tests do not establish scientific truth or child engagement.

Deliver a concise review package: a labelled six-action animation reel at actual video scale;
three full MP4s with SRT captions/thumbnails; versioned authoring/runtime exports, manifest/hashes
and reproducible commands; science evidence/corrections; validation, actual/reserved costs and
remaining limitations. Link/show local media with absolute paths.

Ask for one consolidated creative sign-off on the completed library and pilots. Keep approval
pending until explicitly given; do not reapprove unchanged v1 details. Incorporate corrections
received during work and continue. No YouTube upload before review and explicit upload authorization.

Pause only for unavoidable account/credential/consent or enforced permission actions, completed
creative sign-off, material unresolved science, a budget increase/out-of-scope decision, or
upload/publication authorization. Continue unaffected work while answers are pending. Silence is
not approval. Do not bulk-stage the untracked checkout, commit credentials, or create a Git commit
or push merely because this prompt says “versioned.”
