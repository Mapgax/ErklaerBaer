"""Build the machine-readable index of everything reusable in this project.

Two outputs, both regenerated rather than hand-maintained:

* `ASSETS.json` for an agent: one entry per reusable piece, with where it is, whether it is
  in the repository or local only, what produced it, what it cost, and what it may be used
  for. An agent deciding whether to spend on a new asset should read this first.
* `ASSETS.md` for a person skimming the same thing.

Nothing here reads a credential, and local-only pieces are listed by path and provenance
without being copied anywhere.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("rive-rig", "generated-art", "drawn-art", "font", "template", "audio", "script", "episode")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tracked(path: Path) -> bool:
    """Is this path committed, or ignored and therefore local only?"""
    relative = path.relative_to(ROOT)
    return subprocess.run(["git", "check-ignore", "-q", str(relative)], cwd=ROOT).returncode != 0


def describe(path: Path, **fields) -> dict:
    entry = {"path": str(path.relative_to(ROOT)), **fields}
    if path.is_file():
        entry["bytes"] = path.stat().st_size
        entry["sha256"] = sha256(path)
        entry["in_repository"] = tracked(path)
    elif path.is_dir():
        files = [p for p in path.rglob("*") if p.is_file()]
        committed = [p for p in files if tracked(p)]
        entry["files"] = len(files)
        entry["bytes"] = sum(p.stat().st_size for p in files)
        entry["committed_files"] = len(committed)
        entry["committed_bytes"] = sum(p.stat().st_size for p in committed)
        # A folder can be partly committed: manifests travel, baked frames do not.
        entry["in_repository"] = (
            True if len(committed) == len(files) else ("partial" if committed else False)
        )
    else:
        entry["missing"] = True
    return entry


def rive_rigs() -> list[dict]:
    entries = []
    for rig in sorted((ROOT / "assets/mascot/rig").glob("v*")):
        manifest_path = rig / "manifest.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text())
        actions = {name: len(spec["frames"]) for name, spec in manifest["actions"].items()}
        entries.append(
            describe(
                rig,
                id=f"rive-rig-{rig.name}",
                kind="rive-rig",
                title=f"Bear mascot rig {rig.name}",
                actions=actions,
                fps=manifest.get("fps"),
                crop=manifest.get("crop"),
                pivot=manifest.get("pivot"),
                runtime=manifest.get("runtime", {}).get("file"),
                runtime_sha256=manifest.get("runtime", {}).get("sha256"),
                source_file_id=manifest.get("source_file_id"),
                review_status=manifest.get("review_status"),
                reuse=(
                    "Baked transparent PNG clips for any episode. Neutral loops against the "
                    "global clock; every other action plays once and holds its last frame. "
                    "There is no wave action."
                ),
                regenerate=(
                    "Export .riv from Rive, then "
                    "scripts/rive-bake/serve.py --riv <file> --library <rig dir>"
                ),
            )
        )
    return entries


def generated_art() -> list[dict]:
    """Everything a paid image provider made. These are the expensive pieces to reuse."""
    entries = []
    for source_path in sorted((ROOT / "assets/library").glob("*/v3/source.json")):
        source = json.loads(source_path.read_text())
        folder = source_path.parent
        entries.append(
            describe(
                folder,
                id=f"art-{folder.parent.name}",
                kind="generated-art",
                title=source.get("semantic_id", folder.parent.name),
                provider=source.get("provider"),
                model=source.get("model"),
                seed=source.get("seed"),
                prompt=source.get("prompt"),
                reserved_credits=source.get("reserved_credits"),
                actual_credits=source.get("actual_credits"),
                review_status=source.get("review_status"),
                reuse="Cut out with a transparent alpha; place with paste_prop at any size.",
                regenerate=f"scripts/generate_v3_{folder.parent.name}.py then prepare_v3_*.py",
            )
        )
    return entries


def drawn_art() -> list[dict]:
    entries = []
    for bundle_path in sorted((ROOT / "assets/library").glob("*/v3/bundle.json")):
        folder = bundle_path.parent
        if (folder / "source.json").is_file():
            continue
        entries.append(
            describe(
                folder,
                id=f"art-{folder.parent.name}",
                kind="drawn-art",
                title=folder.parent.name,
                reuse="Layered PNG/SVG parts for the paper-cut collage.",
                regenerate="scripts/index_v3_assets.py",
            )
        )
    return entries


def templates() -> list[dict]:
    from erklaerbaer.models import TEMPLATES

    entries = []
    for template_id, template in TEMPLATES.items():
        entries.append(
            describe(
                ROOT / "src/erklaerbaer" / template.modules[0],
                id=f"template-{template_id}",
                kind="template",
                title=template_id,
                asset_bundle=template.bundle,
                framings=sorted(template.framings),
                summary=template.summary,
                reuse=(
                    "One template renders one mechanism. Register it once in "
                    "models.TEMPLATES and add a branch in the module's draw(); every "
                    "geometry derives from a View."
                ),
            )
        )
    entries.append(
        describe(
            ROOT / "src/erklaerbaer/gas.py",
            id="gas-motion",
            kind="template",
            title="Deterministic gas inside any outline",
            summary=(
                "Precomputes a reflecting path per particle and looks positions up by "
                "distance travelled, so speed and container shape stay independent."
            ),
            reuse="Any shot needing particles that must never leave a drawn shape.",
        )
    )
    return entries


def audio() -> list[dict]:
    return [
        describe(
            ROOT / "scripts/build_brand_intro.py",
            id="audio-bookends",
            kind="audio",
            title="Brand intro, outro and jingle",
            summary=(
                "One script renders both bookends so they cannot drift apart. The closing "
                "phrase is the opening melody resolving to its tonic."
            ),
            provenance="Original local additive synthesis; no samples and no provider call",
            reuse="--duration and --outro-duration set their lengths; --language picks the card.",
        ),
        describe(
            ROOT / "src/erklaerbaer/sounds.py",
            id="audio-sound-anchors",
            kind="audio",
            title="Local sound anchors",
            summary=(
                "pluck, thud and arrival for the guitar; clack, settle and escape for the "
                "coin; knock, double_knock and crunch for falling objects. Each sits in "
                "measured silence and names something the picture does."
            ),
            provenance="Synthesized locally from numpy; no samples",
            reuse=(
                "Name the shape in the episode's SoundEvent in episodes.py; the mixer "
                "refuses an anchor outside 20 to 25 dB under speech."
            ),
        ),
        describe(
            ROOT / "src/erklaerbaer/audio.py",
            id="audio-speech-repair",
            kind="audio",
            title="Speech post-processing",
            summary=(
                "collapse_internal_silence shortens pauses a voice inserts inside a line; "
                "keep_first_utterance drops a repeated reading of a short line."
            ),
            reuse="Both run on cached audio, cost nothing, and are covered by tests.",
        ),
    ]


def fonts() -> list[dict]:
    folder = ROOT / "assets/fonts/berner-basisschrift"
    notice = folder / "NOTICE.txt"
    return [
        describe(
            folder,
            id="font-berner-basisschrift",
            kind="font",
            title="Berner Basisschrift 1",
            licence="SIL Open Font Licence; see NOTICE.txt",
            licence_note=notice.read_text().splitlines()[0] if notice.is_file() else None,
            reuse=(
                "Every child-facing word. Chosen for coverage and licence: it is the only "
                "candidate with an eszett, accented Latin vowels and a commercial licence."
            ),
        )
    ]


def episodes() -> list[dict]:
    catalog = ROOT / "catalog/videos.json"
    entries = []
    for board in sorted((ROOT / "storyboards/v3").rglob("*.json")):
        data = json.loads(board.read_text())
        entries.append(
            describe(
                board,
                id=f"storyboard-{data['experiment_id']}-{data['language']}",
                kind="episode",
                title=data.get("localized_title"),
                language=data["language"],
                template=data["scenes"][0]["shot"]["template_id"],
                scenes=len(data["scenes"]),
                science_review=f"docs/evidence/v3/{data['experiment_id']}.review.json",
                reuse=(
                    "Reviewed narration. Any text change needs a fresh science review and "
                    "re-records the affected lines."
                ),
            )
        )
    if catalog.is_file():
        entries.append(
            describe(catalog, id="catalog-videos", kind="episode", title="Build catalogue")
        )
    return entries


def main() -> None:
    entries = (
        rive_rigs() + generated_art() + drawn_art() + templates() + audio() + fonts() + episodes()
    )
    index = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "generator": "scripts/index_reusable_assets.py",
        "note": (
            "Read this before generating a new asset. `in_repository` false means the piece "
            "exists on the owner's machine but is deliberately not committed, either because "
            "it is large and derived or because it is private; `regenerate` says how to "
            "rebuild it. Costs are recorded so reuse can be weighed against a new call."
        ),
        "kinds": list(KINDS),
        "entries": entries,
    }
    (ROOT / "ASSETS.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# Reusable pieces",
        "",
        "Generated by `scripts/index_reusable_assets.py`. `ASSETS.json` is the machine-readable",
        "version and is what an agent should read before spending on a new asset.",
        "",
        "A piece marked **local only** exists on the owner's machine but is not committed,",
        "because it is large and regenerable or because it is private.",
        "",
    ]
    for kind in KINDS:
        chosen = [e for e in entries if e.get("kind") == kind]
        if not chosen:
            continue
        lines += [f"## {kind}", "", "| piece | where | size | notes |", "|---|---|---|---|"]
        for entry in chosen:
            state = entry.get("in_repository")
            suffix = {True: "", "partial": " *(manifests only)*"}.get(state, " *(local only)*")
            where = entry["path"] + suffix
            size = f"{entry.get('bytes', 0) / 1048576:.1f} MB" if entry.get("bytes") else "-"
            note = entry.get("reuse") or entry.get("summary") or entry.get("title") or ""
            lines.append(f"| {entry.get('title', entry['id'])} | {where} | {size} | {note} |")
        lines.append("")
    (ROOT / "ASSETS.md").write_text("\n".join(lines))
    print(f"{len(entries)} entries -> ASSETS.json and ASSETS.md")


if __name__ == "__main__":
    main()
