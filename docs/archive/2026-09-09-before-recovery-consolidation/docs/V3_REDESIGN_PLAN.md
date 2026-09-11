# Approved v3 redesign plan

Approved by the owner on 2026-09-08. Executable handoff:
[PRODUCTION_V3_PROMPT.md](PRODUCTION_V3_PROMPT.md).

## Decisions

- Paper/felt collage, matching the bear and retaining the calm background.
- One video per week, alternating languages by completed production slot.
- Complete Dutch guitar benchmark first; German follows when the weekly queue starts.
- Dedicated authenticated read-only MINT Nochmal feed; deployment is separate.
- Trial expressive Google TTS with narrator and gentle bear question voice; no lip-sync.
- Preserve remaining task caps; no automatic recurring allowance or provider purchases.
- Reusable locally indexed artwork, Rive sources/runtime exports and transparent animation bundles.

## Findings and acceptance matrix

| Feedback/finding | Required correction and evidence |
|---|---|
| Science resembles basic document shapes | Layered recognizable props, purposeful close-ups/reveals, and a complete animated guitar benchmark |
| Guitar supports/hole ambiguous; ear unrecognizable | Coherent attachments and perspective; recognizable top hole and ear at viewing scale |
| Box-to-air explanation weak | Visible string → attachments → box surface → locally oscillating air → ear sequence |
| Bear too small | Size from visible bounds with stable crop/pivot; larger question shots |
| Magnifying-glass rim broken | Trace source/cleanup/mesh/bake cause; inspect repaired rim throughout animation |
| Voice flat despite acceptable pace | Short expressive German/Dutch comparisons; distinct gentle bear voice; listening review |
| Bottle resembles jar; warming hands absent | Narrow-neck bottle, visible hands and precisely attached heat cues |
| Gas never hits walls | Collision geometry follows rendered interior and coin; continuous physical stages |
| Stone/ground hard to read | Restrained textured layers with clear contact, scale and reveal |
| Spider proportions and woodlouse markings wrong | Anatomical inspection; clipped markings and exact adult leg counts |
| Counting dots unexplained | Readable 6/8/14 numerals with highlighted legs |
| Background and approximate pace good | Preserve both as the design baseline |
| Technical PASS overstated completion | Separate technical/science/visual/listening statuses; creative revision remains required |
| Build hashes too broad; packager accepts stale identity | Hash render dependencies and verify identity against actual build inputs |

## Production policy

Randomly select uncovered Nochmal topics first. Newly observed uncovered favorites take priority
at the next unstarted slot; randomize ties. Then use older favorites, then uncovered public topics.
Persist selections for retries, alternate languages by completed slots, and do not regenerate covered
topics without an explicit rebuild. Missing favorite data blocks selection. Coverage is topic-level.
Feed and queue state are private; provider calls receive only public topic/script/artwork content.

## Cost and rollout

Remaining at approval: 12 BFL requests, 240 reserved credits, 20 LLM calls, 17,448 TTS characters.
Read the live ledger before spending; this document does not reset it. Add token-aware reservations
for Gemini before its trial. Rive is a fixed subscription; BFL reuse does not regenerate images.
Measure retries, new assets, authoring and review time before recommending higher frequency.

First creative gate: a full redesigned guitar pilot, voice comparison, repaired bear reel, and
indexed assets. After acceptance, reuse the standard for the other pilots and weekly production.
No deployment, publication, activation, purchase, Git commit or push is authorized by this plan.

## Documentation status

The older documents retain useful implementation and historical details. Their v3 notices take
precedence over conflicting daily scheduling or obsolete claims about missing Rive exports. The
implementation must replace affected operational sections as the new behavior becomes real; do not
describe planned interfaces or quality improvements as already implemented.
