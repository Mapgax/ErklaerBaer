# Episode runbook

How one production slot turns a MINT topic into a Private upload. The scheduled runs follow
this file; so does anyone building by hand. Read `CLAUDE.md` first: its lessons are the
review standard every step below is judged against.

**Cadence.** Owner decision, 2026-09-13: German on Monday, Dutch on Thursday, each on a
topic never produced before in any language. The slots live in `config/settings.toml`
under `[production_v3]`.

**What a run may do.** Build, review its own frames and speech, fix what it finds, upload
**Private**, record the result, stop. It never publishes, never commits or pushes, never
raises a budget, and never retries a paid call blindly.

**When a gate fails.** Fix it inside the run if you can. If you can't, stop before the
upload and record what failed and why in `docs/AGENT_STATUS.md`. A missed slot is better
than a wrong video.

## 1. Preconditions

```bash
.venv/bin/python3 -m pytest -q
.venv/bin/python3 -c "import json,datetime;m=json.load(open('catalog/usage.json'))['months'].get(datetime.date.today().strftime('%Y-%m'),{});print(m)"
```

Tests must pass. `gemini_requests` for this month must leave at least 40 of
`monthly_speech_requests` (360) free. Otherwise stop and report; the allowance is the
owner's to change.

## 2. Topic

```bash
.venv/bin/python3 scripts/next_topic.py
.venv/bin/python3 scripts/next_topic.py --take <topic-id>
```

The first command lists unused topics in an order fixed by the slot date, so a retried slot
sees the same list. Take the first one whose mechanism you can show correctly and draw well
within this run. Prefer a topic whose mechanism already has a template in
`models.TEMPLATES`. If you skip a candidate, say why in the run record. `--take` freezes the
MINT snapshot under `docs/evidence/snapshots/` and prints its `source_hash`. The topic
counts as used the moment its storyboard exists.

## 3. Evidence

Write `docs/evidence/<topic-id>.json` in the shape of `docs/evidence/fall-wettrennen.json`:
- `facts`, each with authoritative sources (OpenStax, Britannica, university or museum pages)
- `corrections` wherever MINT simplifies into a contradiction

The script may only claim what a fact supports.

## 4. Template

Only if no registered template shows this mechanism:

1. Register the mechanism in `models.MECHANISMS`: its objects, relationships and beat verbs.
2. Register the template in `models.TEMPLATES`: bundle, mechanism, framings, modules and a
   summary. That is the only registration; the renderer, the validators, the build identity
   and the asset index all read it.
3. Write `src/erklaerbaer/collage_<name>.py` with
   `draw(canvas, scene, seconds, state, *, font, small_font, segments=())` and
   `thumbnail(settings, board, renderer, output_path)`. Model it on `collage_fall.py`:
   - world geometry and timing as named constants
   - one `View` per framing
   - the bear box read from the library via `mascot_origin`
   - no hand-typed position that belongs to another element
4. Assert the geometry and timing relations in `tests/test_<name>_template.py`. Do it in
   tests, never with module-level `assert`.

## 5. Script

Copy `scripts/author_fall_v3.py` to `scripts/author_<topic-id>.py` and write the scenes.

- 6 to 9 scenes. The first is a question, the last a recap. Duration hints come from the
  words at 118 per minute.
- Headings are at most five words. Every scene carries a mechanism with beats on its
  segments.
- The bear is on screen where a face matters and absent for at least half the explanation.
  Use his actions (`neutral lift explain think surprise aha`) only where they mean something.
- German: Swiss spelling (ss, never ß). The validator refuses ß.
- Language for six- to nine-year-olds: plain sentences, no commands to perform an experiment.

Run the author script; the storyboard validator runs before anything is written.

## 6. Science review

```bash
DRY_RUN=false .venv/bin/python3 -c "from erklaerbaer.config import load_settings; from erklaerbaer.models import Storyboard; from erklaerbaer.science_review import review_science; s=load_settings(); print(review_science(Storyboard.model_validate_json(open('<storyboard>').read()), s))"
```

One LLM call, journalled. A rejection or a warning that names a real error means fix the
script and review again.

## 7. Stills gate

Adapt `scripts/preview_v3_fall.py` to the new board. Render stills with synthetic timing,
then look at every scene at several phases, at full size and in the phone-width strip.
Check them against every design and explanation lesson in `CLAUDE.md`:
- overlaps
- edges ending on a straight line
- props that don't look like their names
- causes that move after their effects
- compositions held across scenes

Fix and re-render until clean. Technical validation is not creative acceptance; say which
one you did.

## 8. Episode spec

Add an `EpisodeSpec` to `src/erklaerbaer/episodes.py`:
- `CURRENT_TAKES`
- every `SoundEvent` placed on a moment the picture is doing, with its delay imported from
  the template
- the thumbnail from the template

Up to four anchors. The mixer refuses any outside 20 to 25 dB under speech. Shapes live in
`sounds.py`.

## 9. Speech, then check it

```bash
DRY_RUN=false .venv/bin/python3 scripts/build_episode.py <name> --audio-only
.venv/bin/python3 scripts/check_speech.py <name>
```

Speech is the only paid step. The check fails on any take outside one natural reading. Find
the cause before rendering: a repeated reading, a cut sentence, a padded take. The measured
total must land between 90 and 180 seconds.

## 10. Render and inspect

```bash
.venv/bin/python3 scripts/build_episode.py <name> --cache-only
```

Only a folder with `checksums.sha256` is a finished build. Then:
- Render the stills again on the measured `build/v3/<name>/narration.timing.json`.
- Decode frames just before, at and after every sound event to confirm the picture does
  what the sound says.
- Check `validation.json`: no technical warnings, loudness about −16 LUFS.

## 11. Bookends and upload

```bash
.venv/bin/python3 scripts/build_brand_intro.py --episode artifacts/review-v3/<name>/<build> --language <lang> --duration 6 --outro-duration 4
.venv/bin/python3 scripts/upload_v3_review.py --cut artifacts/review-v3/intro/<cut> --dry-run
DRY_RUN=false .venv/bin/python3 scripts/upload_v3_review.py --cut artifacts/review-v3/intro/<cut>
DRY_RUN=false .venv/bin/python3 scripts/finalize_v3_upload.py --video-id <id> --cut artifacts/review-v3/intro/<cut>
```

The upload is Private with notifications off. Its marker is `episode|cut`, so a re-run
recovers the same video instead of uploading twice. The episode's composed thumbnail is
used. Evidence lands in `artifacts/review-v3/uploads/`.

## 12. Record and stop

Add a dated entry at the top of `docs/AGENT_STATUS.md` with:
- the topic and language
- the Private URL, episode and cut builds
- duration and loudness
- the paid requests used
- what you checked and what you fixed
- anything left open for the owner

Paid promotion and Shorts remix are set by the owner in Studio. Then stop.
