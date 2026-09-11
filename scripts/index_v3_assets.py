"""Editable collage layers and a self-contained local gallery; no remote assets or telemetry."""

from __future__ import annotations

import html
import json

from erklaerbaer.build_identity import sha256
from erklaerbaer.collage_guitar import ear, guitar, guitar_layers
from erklaerbaer.config import load_settings
from erklaerbaer.mascot_library import rig_root


def main():
    root = load_settings().project_root
    bundle = root / "assets/library/guitar/v3"
    bundle.mkdir(parents=True, exist_ok=True)
    layers = guitar_layers()
    for name, art in zip(["body", "soundboard", "supports"], layers, strict=True):
        art.save(bundle / f"{name}.png")
    ear().save(bundle / "ear.png")
    guitar(0, 0).save(bundle / "preview.png")
    # Keep each image as an editable layer; precise geometry is an independent SVG.
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="960" height="610"
viewBox="0 0 960 610">
<g id="body"><image href="body.png" width="960" height="610"/></g>
<g id="soundboard"><image href="soundboard.png" width="960" height="610"/></g>
<g id="supports"><image href="supports.png" width="960" height="610"/></g>
<g id="elastic" fill="none" stroke="#efac75" stroke-width="5"><path d="M258 253 L678 253"/></g>
</svg>"""
    (bundle / "layers.svg").write_text(svg)
    geometry = """<svg xmlns="http://www.w3.org/2000/svg" width="960" height="610"
viewBox="0 0 960 610">
<g id="body" stroke="#947248" stroke-width="3">
<path id="left-wall" fill="#927554" d="M100 180 L230 330 L230 500 L100 350 Z"/>
<path id="front-wall" fill="#be9a65" d="M230 330 L840 330 L840 500 L230 500 Z"/>
<path id="top" fill="#d4b27b" d="M100 180 L710 180 L840 330 L230 330 Z"/>
<ellipse id="top-hole" cx="480" cy="258" rx="103" ry="44" fill="#392c25"/>
</g><g id="supports" fill="#d7b788" stroke="#947248" stroke-width="3">
<path d="M225 222 L243 222 L294 286 L294 309 L276 309 L225 245 Z"/>
<path d="M645 222 L663 222 L714 286 L714 309 L696 309 L645 245 Z"/>
</g><path id="elastic" d="M258 253 L678 253" fill="none" stroke="#efac75" stroke-width="5"/>
</svg>"""
    (bundle / "geometry.svg").write_text(geometry)
    entries = []
    for semantic, folder, tags, preview in [
        ("guitar-v3", bundle, ["guitar", "sound", "box", "collage"], "preview.png"),
        (
            "collage-materials-v3",
            root / "assets/library/materials/v3",
            ["paper", "felt", "texture"],
            "material-sheet.png",
        ),
        ("ear-v3", root / "assets/library/ear/v3", ["ear", "felt", "sound"], "ear.png"),
        (
            "bear-v3-working",
            rig_root(root),
            ["bear", "six actions", "repaired rim"],
            "frames/neutral/0000.png",
        ),
    ]:
        files = {
            str(p.relative_to(folder)): sha256(p)
            for p in sorted(folder.rglob("*"))
            if p.is_file()
            and p.name not in {"bundle.json", "manifest.json"}
            and not p.name.endswith(".request.json")
        }
        entry = {
            "semantic_id": semantic,
            "version": "3",
            "tags": tags,
            "files": files,
            "preview": str((folder / preview).relative_to(root / "assets")),
            "review_status": "provisional",
            "owner_approved": False,
            "source": "BFL texture with deterministic editable geometry"
            if semantic == "guitar-v3"
            else "see source manifest",
            "anchors": {"elastic_left": [258, 253], "elastic_right": [678, 253]}
            if semantic == "guitar-v3"
            else {},
            "dimensions": [960, 610] if semantic == "guitar-v3" else None,
            "limitations": ["Rive prop animation source/runtime pending desktop connection"]
            if semantic == "guitar-v3"
            else [],
        }
        if semantic == "bear-v3-working":
            m = json.loads((folder / "manifest.json").read_text())
            entry.update(
                actions=list(m["actions"]),
                fps=m["fps"],
                dimensions=m["dimensions"],
                pivot=m["pivot"],
                crop=m["crop"],
                limitations=m["limitations"],
                dependencies=[m["runtime"]["sha256"]],
                review_status=m["review_status"],
            )
        if semantic in {"collage-materials-v3", "ear-v3"}:
            entry.update(json.loads((folder / "source.json").read_text()))
        (folder / "bundle.json").write_text(json.dumps(entry, indent=2) + "\n")
        entries.append(entry)
    gallery = root / "assets/gallery"
    gallery.mkdir(exist_ok=True)
    (gallery / "index.json").write_text(json.dumps(entries, indent=2) + "\n")
    cards = "".join(
        f'<article data-search="{html.escape(" ".join([e["semantic_id"], *e["tags"]]))}">'
        f'<img src="../{e["preview"]}" alt="{html.escape(e["semantic_id"])}">'
        f"<h2>{html.escape(e['semantic_id'])}</h2><p>{html.escape(e['review_status'])}</p>"
        f"<p>{html.escape('; '.join(e['limitations']))}</p></article>"
        for e in entries
    )
    (gallery / "index.html").write_text(
        """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>ErklaerBaer asset library</title>
<style>body{margin:4vw;background:#f8efd8;color:#344744;font:17px system-ui}h1{font-size:34px}
input{padding:14px;border:1px solid #839b91;border-radius:9px;font:inherit;width:min(85%,550px)}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;margin-top:30px}
article{background:#fffcf3;border-radius:15px;padding:24px}img{height:260px;width:100%;object-fit:contain}
h2{font-size:21px}p{line-height:1.5}article[hidden]{display:none}</style>
<h1>ErklaerBaer asset library</h1><p>Local v3 working library. Creative review is pending.</p>
<label for="search">Find an asset</label><br><input id="search" placeholder="guitar, felt, bear…">
<main>"""
        + cards
        + """</main><script>document.querySelector('input').addEventListener('input',e=>{
for(const card of document.querySelectorAll('article')) {
card.hidden=!card.dataset.search.toLowerCase().includes(e.target.value.toLowerCase());
}});</script></html>"""
    )
    print(gallery / "index.html")


if __name__ == "__main__":
    main()
