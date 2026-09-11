# ErklaerBaer

Local science-video production for MINT-Bot. The approved v3 direction is paper/felt collage,
expressive narration and one weekly video, alternating languages by completed slot.
The full Dutch guitar benchmark comes first; its creative gate is still incomplete.

Default dry-run behavior remains enabled. No weekly production, upload or publication is active.
See [current implementation and blockers](docs/V3_IMPLEMENTATION_STATUS.md),
[weekly queue](docs/WEEKLY_V3.md), and [local asset recovery](docs/ASSET_RECOVERY_V3.md).

## Start here

For the authorized six-action mascot and local pilot upgrade, use the
[v3 continuation prompt](docs/PRODUCTION_V3_PROMPT.md). The [specification](docs/SPEC.md) distinguishes
the v2 target from the historical v1 rig and procedural renderer. The current implementation and
resume state are recorded in [the agent checkpoint](docs/AGENT_STATUS.md). Historical editor gates
do not require repeating owner approvals.

1. Read [the specification](docs/SPEC.md), [setup guide](docs/SETUP.md),
   [glossary](docs/GLOSSARY.md), and [legacy prototype review](docs/LEGACY_REVIEW.md).
2. Create a Python 3.12 virtual environment and install the locked dependencies:

   ```bash
   python3 -m venv .venv
   .venv/bin/python3 -m pip install -r requirements.lock
   .venv/bin/python3 -m pip install --no-deps -e .
   ```

3. Fill in the owner-supplied values in `.env` without sharing that file.
4. Check the local setup:

   ```bash
   .venv/bin/python3 -m erklaerbaer doctor --dry-run
   .venv/bin/python3 -m erklaerbaer discover --days 14 --dry-run
   ```

5. Keep `DRY_RUN=true` until Gate 1 in the setup guide is complete.

## Historical CLI commands (automatic jobs disabled)

```bash
python3 -m erklaerbaer doctor
python3 -m erklaerbaer design-mascot --pose neutral --dry-run
python3 -m erklaerbaer prepare-rive-assets --dry-run
python3 -m erklaerbaer setup-youtube
python3 -m erklaerbaer discover --days 14
python3 -m erklaerbaer prepare --days 14
python3 -m erklaerbaer build EXPERIMENT_ID --language de-DE
python3 -m erklaerbaer build EXPERIMENT_ID --language de-DE --rerender
python3 -m erklaerbaer upload EXPERIMENT_ID --language nl-NL
python3 -m erklaerbaer release --date 2026-09-04 --experiment-id EXPERIMENT_ID
```

All commands that could call a paid or write-capable external API accept `--dry-run`. Public MINT
JSON discovery remains read-only network traffic.

## Repository data policy

Versioned: code, configuration, curated source assets, storyboards, captions, thumbnails,
checksums, usage counters, and the small video catalog.

Ignored: `.env`, credentials, narration audio, intermediate files, and rendered MP4 files.

The legacy `create_video.py` and `atom_laser.mp4` are retained as historical prototype inputs;
the new package does not import or execute them.
