# Operating procedure

## Approved weekly target

Follow [the v3 prompt](PRODUCTION_V3_PROMPT.md). Target: one video each Monday morning in
Europe/Berlin, alternating languages by completed slot, with uncovered Nochmal topics first and
new uncovered favorites prioritized. Persist selection for retries; unavailable private feed blocks
selection. Keep queue state private. No production activation or publication is currently authorized.
The weekly selector/feed are planned, not implemented. Daily workflows below describe the retained
legacy implementation and must not be activated as an alternative to the weekly target.

## Historical daily flow

The nightly workflow discovers the next 14 dates and prepares at most five missing versions. A
finished upload is private. In YouTube Studio, review the scientific explanation, visuals, spoken
language, captions, thumbnail, and child-audience suitability; change a passing video to unlisted.

The MINT-Bot morning workflow dispatches the actual resolved date and experiment ID. ErklaerBaer
recomputes the language from the date and looks up the exact current source hash. It publishes
only when that exact video is unlisted. A missing or private item leaves the day without a new
public video.

## Review checklist

- Every factual claim is supported by the preserved MINT source and independently checked local
  fact pack; justified corrections are explicit and the rendered mechanism matches them.
- The video explains the mechanism and does not repeat materials or steps.
- Language is entirely German or Netherlands Dutch as assigned.
- Narration is literal, short, and suitable for ages 6–9.
- At most five words are visible in a scene and all text is inside safe margins.
- The prediction pause is long enough to think but does not drag.
- Captions match the narration and scientific terminology.
- No logos, third-party characters, unlicensed artwork, or generated text appear in visuals.
- Runtime is normally 90–180 seconds and never exceeds five minutes.

## Recovery

The v2 target invalidates reuse when storyboard/evidence, renderer, mascot assets or voice/timing
settings change. Approval belongs to the exact build fingerprint. This migration must be verified
before activation. Provisional assets are allowed only in local review builds; visual rerenders
reuse cached narration. Follow `PRODUCTION_PROMPT.md` for bounded v2 work: provider calls and Rive
authoring writes are already authorized, the completed reel/pilots need consolidated creative
sign-off, and upload remains a separate authorization. Historical per-keyframe gates do not apply.

Interrupted uploads are recovered using the exact marker in the YouTube description. Re-running
`upload` is safe. Duplicate daily dispatches are also safe: an already-public key is a no-op.

If a source explanation changes, its hash changes. The old video remains in the catalog for audit
and reuse is refused. Review and approve the newly generated version.

If OAuth expires or is revoked, run `setup-youtube` again locally and replace the GitHub refresh
token. If a paid-call budget is exhausted, the system stops before the next request; inspect
`catalog/usage.json` and provider dashboards rather than editing counters to bypass the stop.

An automated-review rejection is not retried by the nightly job. Read the stored warnings, correct
the canonical source if necessary, then explicitly request a fresh writing pass:

```bash
python3 -m erklaerbaer build EXPERIMENT_ID --language de-DE --regenerate-storyboard
```

## Incident rules

- Unexpected public video: make it private in YouTube Studio, disable the daily workflow, and
  inspect catalog history before resuming.
- Factual error: make the video private, correct the canonical MINT explanation, and let the new
  source hash force a new review cycle.
- Credential exposure: revoke the affected key or OAuth grant first, then replace GitHub and local
  values. Do not rely on deleting logs or git history.
- Repeated generation failure: retain the storyboard and warnings for diagnosis; never weaken the
  review or publication gate merely to meet the daily cadence.
