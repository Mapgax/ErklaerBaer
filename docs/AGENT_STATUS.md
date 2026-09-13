# Current agent checkpoint

Updated 2026-09-13. Start with [RECOVERY_AND_NEXT_STEPS.md](RECOVERY_AND_NEXT_STEPS.md): exact artifact paths, archives, remaining spending and ordered continuation.

## Review, one pipeline, two episodes a week, 2026-09-13

A bad-day code review of the pilot session found copy-paste, a stale-render bug and budget
counters that could not survive recurring production. All findings are fixed. Each fix was
proven before it replaced what it fixed:
- narration, mixed audio, sound events, thumbnails and 75 sampled frames hashed before and
  after
- guitar and coin byte-identical
- the pilot identical except two intended subpixel and label shifts
- a full cache-only rebuild of the pilot through the new builder, with narration, captions
  and sound events identical to the uploaded video

- **One builder.** `src/erklaerbaer/episode.py` replaces the three copied build scripts, which
  are deleted. Episodes are data in `episodes.py`, sound shapes live in `sounds.py`, and each
  template's thumbnail lives in its module. The command is `scripts/build_episode.py <name>`.
  Rendering the pilot dropped from about four minutes to about two, because shadows are now
  blurred in small patches.
- **One template registry.** `models.TEMPLATES` and `models.MECHANISMS` are the only
  registration. Validators, renderer, build identity and asset index read them.
- **Fixed: stale renders.** Coin builds never hashed `collage_coin.py`, `gas.py` or the hand
  artwork, so a coin template change could return an old video as "Existing exact render".
  Also fixed: an interrupted build left an unsealed folder that would have counted as
  finished; now only a folder with `checksums.sha256` counts.
- **Fixed: floor strip.** It altered the alpha of a cached texture.
- **Monthly budget.** 360 Gemini requests, 750,000 characters and 200 LLM calls per
  calendar month replace the one-time counters (90 total, 79 used). Recorded as an owner
  authorization in `catalog/usage.json`; nothing was reset.
- **Cadence.** German on Monday, Dutch on Thursday, at 07:00, each on a never-used topic.
  - `scripts/next_topic.py` selects the topic.
  - `docs/EPISODE_RUNBOOK.md` is the procedure.
  - `scripts/check_speech.py` is the speech gate.
  - Local scheduled tasks `erklaerbaer-monday-german` and `erklaerbaer-thursday-dutch` run
    it; the first is 2026-09-14. They need the Claude app open.
- **Upload path.** Upload and finalize share `cuts.py`. Finalize merges into the upload's
  record instead of overwriting it, reads made-for-kids from settings, and uses the
  episode's composed thumbnail.
- **Not changed, flagged.** `weekly_queue.py`, the favourites queue, remains unused because
  its feed was never deployed.

95 tests and Ruff pass.

## Pilot on a new topic, rig v5, uploaded Private, 2026-09-12

"Wat valt het eerst?" (`fall-wettrennen`, nl-NL). First episode built end to end on a new
template, and the first to use all six clip-baked bear actions.

- Private: https://youtu.be/1LounhliDRk, 3:08 with bookends. Episode `4c7030cea87d9b93cc47a7a2`,
  177.93 s, -16.0 LUFS, -1.4 dBFS true peak, no technical warnings. Cut
  `050e69ccdfb4af6d35715eb5`. Dutch captions serving, custom thumbnail attached, notifications off.
  Evidence: `artifacts/review-v3/uploads/4c7030cea87d9b93cc47a7a2-050e69ccdfb4af6d35715eb5.json`.
- New template `fall-collage` (`src/erklaerbaer/collage_fall.py`), mechanism `falling-objects`,
  evidence pack `docs/evidence/fall-wettrennen.json`, script generator `scripts/author_fall_v3.py`,
  stills gate `scripts/preview_v3_fall.py`, build `scripts/build_episode.py fall`, geometry tests
  `tests/test_fall_template.py`. Science review (Haiku) approved with no warnings.
- Spend: 25 Gemini speech requests (79 of 90 now used; the repeated line "De klep gaat open." is
  one cached take), one LLM review call. No BFL.
- Workflow faults this run found and fixed: the short-line repeat trimmer cut five single Dutch
  readings mid-sentence (the pilot now trims only a take too slow for its text and caps edge
  silence; coin audio verified identical); the bookend builder required a Rive runtime a clip
  library does not have; finalize only looked in the guitar folder and hard-coded a superseded
  id; both upload scripts overwrote one evidence file (now one file per cut).
- Open, owner: full listening, especially whether "De klep gaat open." is one slow reading;
  creative acceptance; paid promotion and Shorts remix in Studio. Known weak spots: the landed
  and crumple scenes hold one composition for long stretches; the air displacement is subtle.

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
