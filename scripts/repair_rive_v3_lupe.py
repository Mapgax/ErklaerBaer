"""Bind the magnifier to one bone. Refuses v1/v2 and records exact before values.

The owner saw the lens deform as the bear turns his head. The cause is in the neutral
pose's skin: the magnifier's nineteen vertices are split across bones, twelve following
`bone_head` and the rest the torso and root. The bear holds the magnifier in his paw, which
the arm moves, so a head turn drags part of the glass with it and stretches the ellipse.

This rebinds those nineteen vertices to `bone_torso` alone, at full weight. It changes skin
weights only: no raster artwork, no vertex position, no bind rotation and no animation key.
Weights do not affect the rest pose, so a capture before and after must be identical.

Run only with desktop Rive active on v3 duplicate 2564932.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from rive_mcp import call, connect

V3_FILE = 2564932
LOG = Path("build/v3/lupe")
HEAD_BIND_ROTATION = -0.10641551025538434
# Tendon order under the skin is root, torso, head; weight indices are one-based.
TORSO_INDEX = 2
FULL_WEIGHT = 255
# The magnifier, in artboard coordinates, read off the vertex overlay.
RING = (264.0, -206.0)
RING_RADIUS = 128.0
HANDLE_X = (196.0, 250.0)
HANDLE_Y = (-70.0, 40.0)


def checked(name, args):
    result = json.loads(call(name, args)["content"][0]["text"])
    if not result.get("success") or result.get("errors"):
        raise RuntimeError(f"Rive {name} failed: {result.get('errors')}")
    return result


def is_magnifier(x, y):
    if math.hypot(x - RING[0], y - RING[1]) <= RING_RADIUS:
        return True
    return HANDLE_X[0] - 46 <= x <= HANDLE_X[1] + 46 and HANDLE_Y[0] <= y <= HANDLE_Y[1]


def decode(values, indices):
    return [
        ((int(indices) >> (4 * slot)) & 0xF, (int(values) >> (8 * slot)) & 0xFF)
        for slot in range(4)
        if (int(values) >> (8 * slot)) & 0xFF
    ]


def main() -> None:
    connect()
    session = checked("session_info", {})
    if session.get("activeFileId") != V3_FILE:
        raise RuntimeError("Open v3 duplicate 2564932 in desktop Rive; v1/v2 are protected")
    LOG.mkdir(parents=True, exist_ok=True)
    applied = LOG / "applied.json"

    bind = checked("query_property_values", {"propertyKeys": {"0-261": [15]}})
    if abs(bind["values"]["0-261"]["15"] - HEAD_BIND_ROTATION) > 1e-7:
        raise RuntimeError("Unexpected head bind rotation; inspect before editing")

    objects = json.loads(
        call("get_artboard_hierarchy", {"artboardId": "0-29", "depth": 6})["content"][0]["text"]
    )["objects"]
    weights = {o["id"] for o in objects if "Weight" in o["types"]}
    vertices = [o for o in objects if {"ContourMeshVertex", "MeshVertex"} & set(o["types"])]
    pairs = [(v["id"], next(k for k in v["children"] if k in weights)) for v in vertices]

    positions = checked("query_property_values", {"propertyKeys": {v: [24, 25] for v, _ in pairs}})[
        "values"
    ]
    before = checked("query_property_values", {"propertyKeys": {w: [102, 103] for _, w in pairs}})[
        "values"
    ]

    chosen = [(v, w) for v, w in pairs if is_magnifier(positions[v]["24"], positions[v]["25"])]
    if not 15 <= len(chosen) <= 26:
        raise RuntimeError(f"Expected about twenty magnifier vertices, found {len(chosen)}")
    # Re-runnable: only vertices that are not already bound to the torso alone are written,
    # so widening the selection later never rewrites what is already correct.
    todo = [
        (v, w)
        for v, w in chosen
        if before[w]["102"] != FULL_WEIGHT or before[w]["103"] != TORSO_INDEX
    ]
    if not todo:
        print(f"All {len(chosen)} magnifier vertices already bound to bone_torso; nothing to do")
        return

    record = {
        "file_id": V3_FILE,
        "head_bind_rotation": bind["values"]["0-261"]["15"],
        "vertices": [
            {
                "vertex": v,
                "weight": w,
                "x": positions[v]["24"],
                "y": positions[v]["25"],
                "before": before[w],
                "before_decoded": decode(before[w]["102"], before[w]["103"]),
            }
            for v, w in todo
        ],
    }
    history = (
        json.loads((LOG / "before.json").read_text()) if (LOG / "before.json").exists() else []
    )
    if isinstance(history, dict):
        history = [history]
    history.append(record)
    (LOG / "before.json").write_text(json.dumps(history, indent=2) + "\n")

    updates = {w: {"102": FULL_WEIGHT, "103": TORSO_INDEX} for _, w in todo}
    result = checked("set_property_values", {"propertyValues": updates})
    done = json.loads(applied.read_text()) if applied.exists() else []
    if isinstance(done, dict):
        done = [done]
    done.append({"file_id": V3_FILE, "count": len(todo), "updates": updates, "result": result})
    applied.write_text(json.dumps(done, indent=2) + "\n")
    print(
        f"Rebound {len(todo)} magnifier vertices to bone_torso "
        f"({len(chosen)} in the magnifier in total)"
    )
    print("Next: capture to confirm the rest pose is unchanged, then export, bake and measure")


if __name__ == "__main__":
    main()
