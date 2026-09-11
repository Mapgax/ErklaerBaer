# ErklaerBaer v3 implementation prompt

## Objective and authority

Implement the owner-approved paper/felt collage redesign and weekly production plan in
`/Users/andreas/Projects/AI/ErklaerBaer`. The owner approved this plan and saving this prompt on
2026-09-08. Recommended implementation model: GPT-6 Astra, High reasoning.

This prompt supersedes conflicting daily-production and v2-completion instructions in older docs.
Preserve historical reports. V2 passed technical tests but requires creative revision; it is not
owner-approved. Do not mistake approval of this implementation plan for approval of future artwork.

Read `docs/AGENT_STATUS.md`, `docs/SPEC.md`, `docs/RIVE_RIG.md`,
`docs/V3_REDESIGN_PLAN.md`, and the private owner feedback at
`feedback_andreas/Feedback v2 MP4 review.docx`, including its embedded images. Follow applicable
AGENTS.md/session instructions. Inspect Git status before edits; the checkout is largely untracked.
Do not discard owner work or bulk-stage files.

Authorized work: local code/config/docs/assets, bounded existing-provider calls, official loopback
Rive MCP authoring on recoverable duplicates, and a narrow read-only Nochmal integration in the
sibling project `/Users/andreas/Projects/AI/MINT-Bot` where host permissions permit. Inspect that
project's instructions before editing it. Deployment, production activation, uploads, publication,
Git commits/pushes, purchases, top-ups, and new paid providers remain unauthorized.

Keep default dry-run behavior. Use scoped live calls only for authorized local production. Do not
ask the owner to operate timelines or approve each still. Complete and inspect the guitar benchmark
before requesting one consolidated creative review. If an enforced permission/account boundary
blocks one operation, ask for the smallest necessary action and continue independent work.

## Persistent limits

Re-read `catalog/usage.json` before any paid call. At approval, remaining task allowance was:

| Resource | Remaining | Original task cap |
|---|---:|---:|
| BFL requests | 12 | 15 |
| BFL reserved credits | 240 | 300 |
| LLM calls | 20 | 24 |
| TTS characters | 17,448 | 30,000 |

These are remaining amounts, not new allowances; retries/resumes do not reset them. Actual previous
BFL cost was 22.5 credits across three images; 60 credits were reserved. Reserve conservatively,
recover uncertain submissions, and keep actual costs separate. Existing monthly/provider limits
also apply. No automatic increase or recurring budget is authorized.

Gemini-TTS has token billing: retain the character allowance as an additional guard, count delivery
prompts conservatively, and add explicit input/audio-token and USD accounting before synthesis.
Do not infer unlimited output spending from a character cap. Bound the trial and each request using
documented limits and conservative reservations; stop for an explicit cost decision if a safe bound
cannot be established. Check existing Google Cloud access without exposing credentials.

## Delivery sequence

1. Protect feedback, record the approved direction, and verify baseline assets/runtime and caps.
2. Establish the new design with a complete Dutch guitar video, repaired bear, short voice comparison,
   indexed reusable asset bundle, and measured quality/cost report. This is the first creative gate.
3. In parallel only within a single agent's ordinary work, prepare/test the weekly queue and the
   read-only feed without deploying them. Do not spawn agents unless the owner separately asks.
4. After benchmark creative acceptance, reuse its visual standard for coin and safari corrections
   within remaining caps, then prepare weekly production. Report any budget-constrained remainder.
5. Weekly production defaults to one video, alternating languages by completed slot. No automatic
   activation or publication. Recommend greater frequency only from measured results.

## Visual design and science

Keep the calm textured background, limited palette, approved bear identity, and broadly existing
pacing. Build recognizable layered paper/felt collage props with restrained shadows and depth.
BFL creates texture/artwork; editable masks/SVG/layers establish precise geometry; Rive provides
reusable object animations. Keep deterministic particles and scientific motion in code and assemble
with the existing Python compositor. Do not add a generative-video subscription or rewrite the
whole pipeline. More attractive still images alone do not satisfy the animation objective.

### Guitar benchmark

- Replace the box with coherent perspective, visibly attached supports, and an unmistakable top
  sound hole. Use a recognizable ear illustration.
- Show elastic displacement and release, transmission at the attachments, vibrating box surface,
  nearby air oscillation and propagation toward the ear. Air particles oscillate locally rather
  than flying from box to ear; the box does not create energy.
- Use establishing views, close-ups, reveals, and quiet holds, synchronized to measured speech.
  Add a restrained pluck/sound demonstration, with clear separation between slowed visual motion
  and actual sound frequency. Avoid arbitrary attention-grabbing effects or background music.
- Deliver a complete 90–180-second Dutch video, not a teaser or contact sheet.

### Bear and composition

- Locate the magnifying-glass rim defect by comparing approved source, alpha cleanup, mesh, bind
  pose, and baked frames. Repair the actual cause, not a crop hiding it. Preserve v1 master 2558769;
  create a recoverable v3 duplicate from the current v2 working file 2561970 before further authoring.
- Use a fixed library crop and pivot based on visible bounds; never crop each frame independently.
  Size the visible bear, not its transparent source canvas. Inspect at intended video scale.
- Use larger question/reaction shots and unobstructed science close-ups. Keep the bear absent for
  at least half the explanatory runtime. Shared detailed shots retain at least 70% usable science
  width; dedicated bear shots can be larger. Do not keep a permanent side column.
- Preserve six semantic actions and accepted identity. The Lift artwork contains a held stone;
  do not animate another stone as if it were held by the same pose. No walking/gaze/lip-sync system.

### Coin follow-up

Use a recognizable narrow-neck bottle and visible warming hands. Attach heat/pressure cues to
their actual sources and targets. Replace the invisible inset collision rectangle with the actual
interior boundary, including shoulder/neck and coin contact. Maintain fixed bottle volume, faster
mean particle motion, pressure difference, lift, escaping air, pressure reduction, and reset.
Use molecules/air particles rather than inaccurately identifying every point as an atom.

### Safari follow-up

Use recognizable stone and ground layers with restrained texture and correctly proportioned animals.
Correct spider anatomy and clip woodlouse markings inside its silhouette. Show readable numerals
6, 8, and 14 alongside highlighted legs rather than unexplained dots. Check anatomy independently
of generated artwork. Preserve qualifications: adult animals, no universal hiding/rolling claims.

## Expressive narration

Trial Google Cloud Gemini 2.5 Flash TTS against cached Chirp narration using short German and Dutch
samples. Select a warm female narrator and distinct gentle bear voice for two or three short
questions/reactions. Avoid cloning, caricature, exaggerated acting, or lip-sync. Preserve deliberate
prediction pauses and roughly the existing pace, with restrained curiosity/emphasis/satisfaction.

Add declarative speaker roles and delivery profiles to validated speech segments. Cache identity
must include model/provider, voice, speaker, instructions, text, language and audio settings. Persist
measured timings; visually rerender without TTS/writer calls. A model change invalidates only affected
audio identities. Inspect actual listening samples where tools permit and disclose any unverified
pronunciation, emotion or speaker consistency. Do not use tests as a substitute for listening.

## Reusable asset library and interfaces

Create versioned bundles with editable layers/SVG, original inputs, `.rev`, `.riv`, RGBA exports,
previews, checksums, and manifests. Use the existing official fixed-step runtime helper for baking.
Avoid adding Rive as an unattended cloud dependency for each weekly render.

Index semantic asset IDs/version, tags, actions, anchors/pivots, dimensions/FPS/durations, dependencies,
source/model/seed/prompts, cost, review state and limitations. Build a searchable local HTML gallery;
no hosted service or database is needed initially. Keep binaries local with a documented backup and
restore procedure. Separate secrets/request journals/private feedback from index and delivery.

Extend the validated storyboard with template/version references, shot framing, semantic animation
cues and speaker roles. Data must not execute arbitrary code. Share timing-aware template assets
across languages without stretching authored one-shots to fit narration.

Correct build identity: v2 hashes every Python file, while the review packager does not recompute
current identity. Hash actual pixel/audio dependencies, selected templates/assets/evidence/voices,
exclude mutable review state and machine paths, preserve old versions, and reject stale packages.
Approvals must identify exact builds and assets; approval itself must not change the fingerprint.

## Weekly Nochmal queue

MINT favorites are private server state, not the public schedule or `nochmalTauglich` eligibility.
The existing `/api/state` mixes favorites with family history, and search results have a 40-item
limit. Do not use either as the production favorites feed.

Add a dedicated GET-only authenticated endpoint in MINT returning all eligible Nochmal topic IDs
and a stable snapshot revision. Follow actual MINT Nochmal semantics. Use a separate read-only
credential that cannot authenticate existing write endpoints. Return no history, child data, database
credentials, or unrelated fields. No public cache. Keep existing MINT experiments/schedule unchanged.

Queue behavior:

- Initial selection is random among current Nochmal topics lacking an accepted v3 video.
- Newly observed uncovered favorites outrank the older favorite backlog at the next unstarted slot;
  randomize ties. Then consume older uncovered favorites, then uncovered public experiment topics.
- Persist observations, selection, reason, source hash, language, random seed and slot state atomically.
  Retries reuse the selection and cache; concurrent runs cannot select/spend twice.
- Running work stays fixed. Removing a favorite changes future priority, not completed artifacts.
  A covered favorite does not regenerate automatically; rebuilding is explicit. Coverage is topic-level.
- Missing/stale/malformed favorite data blocks selection rather than pretending the list is empty.
  Unknown IDs are reported. If all topics are covered, report exhaustion; do not repeat silently.
- Alternate language by completed slot, not date parity. Dutch guitar is the benchmark; German is next.
  A failed/retried slot retains its language. Default weekly slot is Monday morning, Europe/Berlin.
- Keep weekly automation disabled pending activation authorization. Existing daily workflows must not
  remain an alternative automatic path once the weekly system is activated. Preserve old release data.
- Favorite state and queue details stay local/private and are never sent to BFL/TTS or included in
  public deliverables. Use public topic content only for script/design provider calls.

## Acceptance, documentation and handoff

Maintain a feedback-to-fix matrix. Inspect actual full-resolution MP4 frames and transitions, not
only still compositions. Verify object recognition, connections, anatomy, magnifier rim, bear scale,
science causality, synchronized motion, readable numbers, pacing and narration. Technical checks:
alpha/edges/anchors, loops/one-shots, codec/loudness/captions, deterministic output, cache-only
rerenders, invalidation, approval isolation, and queue/auth/concurrency failure scenarios.

Update all affected Markdown docs under `docs/`: distinguish current implementation from the v3
target, supersede daily instructions, document private feed/token handling, asset recovery, token
costs, current caps and limitations. Keep `AGENT_STATUS.md` current with tools/how, lessons, completed
work, evidence and next steps. Preserve original private feedback and historical v1/v2 reviews.

Deliver the complete guitar MP4/SRT/thumbnail, concise voice comparison, corrected six-action reel,
indexed source/runtime asset bundles, evidence/corrections, checksums, validation and actual/reserved
costs, reproducible commands, and code-only handoff excluding private material. Request consolidated
creative review before wider production. A technical PASS must never be described as creative approval.

Measure generation count/retries, authoring time, cache reuse and review effort per episode. The first
weekly cadence controls quality/workload; additional videos may be cheap in provider charges but
are not assumed cheap in authoring effort. Propose recurring limits after the benchmark; do not renew
this one-time allowance or increase cadence automatically.

## Pricing and model references checked during planning

- BFL FLUX.2: https://bfl.ai/pricing?category=flux.2
- Rive: https://rive.app/pricing (Cadet listed $9/seat/month; native Libraries on Voyager).
- Google: https://cloud.google.com/text-to-speech/pricing (Gemini 2.5 Flash TTS input $0.50/M
  text tokens, output $10/M audio tokens, 25 audio tokens/second at planning time).
- Google expressive TTS: https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
- Implementation model: https://developers.openai.com/api/docs/models/gpt-6-astra

Prices/availability are planning evidence, not guaranteed account terms; verify before paid use.
