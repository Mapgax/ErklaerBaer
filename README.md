# ErklaerBaer

Short science videos for children of about five to nine, in Dutch and German. A felt bear
introduces a question, a paper-cut collage explains the mechanism honestly, and a recap
closes it. Narration is text-to-speech and is disclosed as such in every description.

Two episodes are published: **NL, Hoe een kartonnen gitaar klinkt** and
**DE, Warum die Münze hüpft**.

## Where to start

| If you want to | Read |
|---|---|
| Know what good looks like here | [CLAUDE.md](CLAUDE.md), the "What makes a good video" section |
| Reuse something instead of making it again | [ASSETS.md](ASSETS.md) and machine-readable [ASSETS.json](ASSETS.json) |
| Know the current state | [docs/AGENT_STATUS.md](docs/AGENT_STATUS.md) |
| Continue after reopening the project | [docs/RECOVERY_AND_NEXT_STEPS.md](docs/RECOVERY_AND_NEXT_STEPS.md) |
| See what each review taught | [docs/VISUAL_LESSONS_V3.md](docs/VISUAL_LESSONS_V3.md) |
| Understand the bear rig | [docs/RIVE_RIG.md](docs/RIVE_RIG.md) |

## How an episode is made

1. A storyboard under `storyboards/v3/` holds the narration, the shot per scene and the
   mechanism beats. Its text is reviewed for scientific accuracy before anything is built,
   and the review is journalled in `docs/evidence/v3/`.
2. A template in `src/erklaerbaer/` draws every frame from authored geometry. There is one
   template per mechanism: `collage_guitar` for the vibrating string, `collage_coin` for gas
   pressure.
3. Speech is synthesized once per line and cached, so a rebuild costs nothing.
4. `scripts/build_v3_*.py` renders the episode; `scripts/build_brand_intro.py` adds the
   shared intro and outro; `scripts/upload_v3_review.py` uploads it Private.

Publishing is the owner's action. Agent uploads stay Private.

## Running it

Python 3.12 and the locked environment:

```bash
python3 -m venv .venv && .venv/bin/python3 -m pip install -r requirements.lock
.venv/bin/python3 -m pip install --no-deps -e .
.venv/bin/python3 -m pytest -q
```

`DRY_RUN` defaults to true, so nothing paid or outward-facing happens by accident. Set it on
the single command that needs it, never in `.env`.

## What is not in this repository

It is public, so it holds code, documentation, storyboards, manifests and the small shared
art. It deliberately does not hold secrets, the spending ledger, private owner feedback,
finished video bundles, or the baked mascot frames and Rive binaries, which run to hundreds
of megabytes. [ASSETS.md](ASSETS.md) lists those anyway, with the command that rebuilds
each one, so nothing is invisible just because it is local.

Those local files are not backed up by this repository. They need the owner's own backup.
