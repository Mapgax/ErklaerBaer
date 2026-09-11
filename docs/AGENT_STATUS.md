# Current agent checkpoint

Updated 2026-09-10. Start with [RECOVERY_AND_NEXT_STEPS.md](RECOVERY_AND_NEXT_STEPS.md): exact artifact paths, archives, remaining spending and ordered continuation.

## Completed

- Full Dutch guitar: `cedfada8807f70f3fe6b4a2c`, 175.03 seconds, Gemini narrator and revised conversational bear delivery.
- Corrected native v3 duplicate 2564932, full `.rev` and `.riv`, six actions / 419 baked frames, all 120 neutral rim frames inspected. v1/v2 preserved.
- Reusable 12-second intro and original locally synthesized jingle; corrected build `fb10cd42eb4001c23272e5ef`. Full cut 187.03 seconds.
- Private upload https://youtu.be/z_1Fx6L3N_Q verified in channel content. Dutch captions saved; made for kids; notifications disabled; copyright check found no issues.
- Technical validation, media/checksum checks, sampled shot/transition inspection; 70 Python tests and Ruff passed during production changes. Full listening remains unverified by the agent.

## Current build, uploaded Private

Owner reviews on 2026-09-10 named the air-shot faults, then the cutaway crossing and the
missing pitch comparison, then asked for a reusable outro. All are fixed and measured; see
lessons 10 to 16 in [visual and audio lessons](VISUAL_LESSONS_V3.md).

- Episode `91e84166ea5e825f5708be6d`, 175.03 s, cached narration, zero paid calls.
- Full cut, 6-second intro and 4-second outro: `83b590797703f359139a51fa`, 185.06 s,
  -15.8 LUFS, -1.4 dBFS true peak, 1080p30, h264/aac.
- **Uploaded Private: https://youtu.be/G_WEzJHoN5I.** Dutch captions serving, custom
  thumbnail applied, NL playlist, YouTube duration 3:06. Evidence in
  `artifacts/review-v3/youtube-private-upload-v2.json`.
- Air is a radial field spreading outward from the box face, feathered into the paper. A
  point moves only along the line away from the source and only after the front arrives.
- The coupling is a bow of the face itself, pinned to the box corners.
- Props are authored at the size they are shown; nothing is enlarged after drawing.
- The air is introduced under the heading that names it, still and labelled, before the
  first push. Scene 3's second beat pulls out to the whole box.
- The ear cutaway derives every drawn part from its rim, so no stroke can cross it.
- Scene 5's second beat compares two rates: same speed, different ring spacing.
- The outro answers the intro card: same oval and wordmark, the `aha` raised paw in place
  of a wave, "Tot ziens!" for the tagline, and the opening phrase resolving to its tonic.
- 73 Python tests and Ruff pass.

**The bear rig has no wave action.** Its six baked actions are neutral, lift, explain,
think, surprise and aha. A real wave needs a new action authored in Rive and re-baked; the
outro uses `aha` deliberately and says so in the code.

**Standing upload settings** live in `[youtube]` in `config/settings.toml` and are applied
by `standard_snippet` / `standard_status`: category Education, Dutch as video and audio
language, standard YouTube licence, embedding allowed, altered-content flag false, made for
kids, notifications off, private. Two settings are not exposed by the Data API and are set
in Studio after each upload: paid promotion declared none, and Shorts remix not allowed.

**The upload marker keys on the cut, not the episode.** Two cuts of one episode, with and
without an outro, would otherwise share an identity and a re-run would recover the wrong
video. `scripts/upload_v3_review.py` builds it as `episode|cut`, and `upload_private` now
waits for YouTube to finish processing before writing captions and the thumbnail, so the
whole upload is one command.

**The channel has a first public video.** The owner published `e7qRQqXTfjE` themselves on
2026-09-10, the 3:02 cut with the 6-second intro and no outro, and edited its description at
release. That edit is why its content marker reads `[ERKLAERBAER:karton-gitarre|nl-NL]`
rather than the full five fields. There was no defect. Treat the marker as a build-time
recovery aid only: once the owner edits a description at release, marker matching for that
video is gone, and `artifacts/review-v3/youtube-private-upload-v2.json` is the record that
matters.

Public release is now something the owner does, at a time of their choosing. Agent uploads
stay Private unless the owner says otherwise on the specific video.

## German coin episode, fourth pass, on the corrected rig

- **https://youtu.be/gYSsfjWY9CU**, Private, 2:58. Episode `f1b6a02ca940def7047360b9`, cut
  `e89449e750236c4435bdccf4`, 177.26 s. German captions, custom thumbnail, DE playlist, paid
  promotion none, remix disallowed.
- **The magnifier no longer deforms.** Its twenty vertices were split across bones, twelve
  following `bone_head` while the bear holds it in his paw. All twenty are now bound to
  `bone_torso`. The lens axis ratio across the neutral loop went from a 2.7% spread to 1.0%.
  See [the rig notes](RIVE_RIG.md) for the method and the measurements.
- Rig v4 is installed and selected by `RIG_VERSION` in `mascot_library.py`. Rig v3 is kept
  untouched so the published Dutch episode remains exactly reproducible.
- Swiss spelling, the recap wording and the owner-chosen bottle, lid, halo pressure cue and
  cool tint are all carried forward from the third pass.

**Open.** The published Dutch episode still uses rig v3 and therefore still has the
deforming magnifier. Rebuilding and republishing it is an owner decision.

Superseded Private uploads `M7vpfilsF1o`, `RTKjZP9qeyY` and `pXpVeXA-LHw` are untouched.

## Repository published, 2026-09-11

The project is on GitHub at https://github.com/Mapgax/ErklaerBaer, which is **public**.

- `ASSETS.json` and `ASSETS.md` are the reusable index, regenerated by
  `scripts/index_reusable_assets.py`. Read the JSON before generating any new asset: it
  records provenance, cost and how to rebuild each piece, including the ones deliberately
  left out of the repository.
- `.gitignore` keeps secrets, the spending ledger, private owner feedback, finished video
  bundles and the baked mascot frames and Rive binaries out. A commit is about 16 MB.
- The original single-script video moved to `legacy/` with a note. It shares no code with
  the pipeline.
- Both production workflows stay hard-gated with `if: false`. Only CI runs on a push.

**The local workspace is not backed up by the repository.** Artifacts, baked frames, Rive
binaries, the speech cache and the ledger exist only on the owner's machine.

## Both episodes rebuilt on rig v4

The magnifier fix applies to every episode, so the Dutch one was rebuilt too. Both are
Private and ready to replace what is live.

| Episode | New, Private | Currently public, old rig |
|---|---|---|
| NL guitar | https://youtu.be/mS6j6ph3WSU, 3:06 | https://youtu.be/G_WEzJHoN5I |
| DE coin | https://youtu.be/gYSsfjWY9CU, 2:58 | https://youtu.be/pXpVeXA-LHw |

The Dutch rebuild, episode `4cf5706379bd3571dfd9c8ea` and cut `8e2dbee7114d0a1a26c093d1`,
is the published build with only the rig changed. Duration, loudness, true peak and all
four sound anchors are identical. Of the six baked actions only `neutral` changed, because
the magnifier appears nowhere else, and decoded frames of scenes without the neutral bear
are pixel-identical. In scene 1 the heavy differences sit on the magnifier, centroid
(584, 477).

Publishing and retiring the old videos are the owner's actions. Nothing public was touched.

## Superseded revision

### Revision in review, not uploaded

Owner-requested rework of the air/wave explanation, plus school-script lettering and restrained
sound anchors. See [visual and audio lessons](VISUAL_LESSONS_V3.md) for the measured rules.

- Episode `18805514b7a5d97a7de8b683`, 175.03 s, same voices and cached narration, zero paid calls.
- Combined cuts on that episode: `2f583096ba312608e5b23a36` with the 12-second intro, 187.03 s,
  and `4f5e409cbafc224f0b946b96` with a 6-second intro variant, 181.03 s. Both -15.8 LUFS,
  -1.4 dBFS true peak, no technical warnings.
- Pen-drawn reveal of the air corridor, larger particles with travelling density cushions, a
  separate ear shot with a drawn eardrum, four local sound anchors, composed thumbnail.
- Child-facing words set in Berner Basisschrift 1, vendored at `assets/fonts/berner-basisschrift/`
  with its notice; its hash feeds the build fingerprint.
- The uploaded Private video still carries `cedfada8807f70f3fe6b4a2c`. Nothing was re-uploaded.

## Open

- Native reusable guitar prop `.rev`/`.riv` animation assets are unfinished. Delivered science motion uses the deterministic compositor.
- Consolidated owner audiovisual/creative acceptance. Coin/safari remain behind complete guitar acceptance.
- Nochmal feed deployment, inherited TLS issue, dedicated read-token setup, generalized coverage, unattended runner and weekly activation remain later work. The YouTube API refresh token is now configured.

## Authority and limits

The original `PRODUCTION_V3_PROMPT.md` remains the implementation authority. Subsequent owner instructions explicitly allowed polishing and privately uploading this one review and adding its short jingle intro. Public release, recurring activation, purchases and commits/pushes remain unauthorized. Do not infer acceptance from upload success.

Live ledger: `catalog/usage.json`. Remaining: BFL 10 requests / 200 reserved credits; LLM 19 calls; TTS 10,571 characters. Gemini 18/20 requests, 4/4 trials, $3.022848/$3.358720 reserved, actual billed USD unknown. No budget reset on resume/restore. Do not request Google, native-save or file-URL permissions again; all three are resolved.

## Historical checkpoints

Previous content is preserved byte-for-byte at `archive/2026-09-09-before-recovery-consolidation/docs/AGENT_STATUS.md`; the archive index records SHA-256. It contains obsolete blockers, not current instructions. Current machine records are `artifacts/review-v3/continuation-status.json`, `validation.json` and `youtube-private-upload.json`.
