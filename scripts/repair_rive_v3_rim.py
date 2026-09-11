"""Recoverable rim-contour edit: refuses v1/v2 and records exact before values.

Run only after desktop MCP is active on v3 duplicate 2564932. This changes the
mesh/UV coverage, not the raster artwork, bind rotations or accepted animation.
"""

from __future__ import annotations

import json
from pathlib import Path

from rive_mcp import call, connect

V3_FILE = 2564932
LOG = Path("build/v3/rim-repair")


def checked(name, args):
    result = json.loads(call(name, args)["content"][0]["text"])
    if not result.get("success") or result.get("errors"):
        raise RuntimeError(f"Rive {name} failed: {result.get('errors')}")
    return result


def main():
    connect()
    session = checked("session_info", {})
    if session["activeFileId"] != V3_FILE:
        raise RuntimeError("Open v3 duplicate 2564932 in desktop Rive; v1/v2 are protected")
    LOG.mkdir(parents=True, exist_ok=True)
    completed = LOG / "applied.json"
    if completed.exists():
        print("Contour edit already applied; inspect, export and bake rather than repeat")
        return
    before = checked(
        "query_property_values",
        {"propertyKeys": {"0-120": [24, 25, 215, 216], "0-225": [24, 25, 215, 216], "0-261": [15]}},
    )
    (LOG / "before.json").write_text(json.dumps(before, indent=2) + "\n")
    if abs(before["values"]["0-261"]["15"] - (-0.10641551025538434)) > 1e-7:
        raise RuntimeError("Unexpected head bind rotation; inspect before editing")
    # Move the two inward-cutting contour vertices just outside the source silhouette.
    # UVs move with geometry, so the original alpha/raster determines the exact outer edge.
    updates = {}
    for oid, x, y in [("0-120", 695.0, 410.0), ("0-225", 730.0, 380.0)]:
        updates[oid] = {"24": x - 512, "25": y - 680, "215": x / 1024, "216": y / 1360}
    result = checked("set_property_values", {"propertyValues": updates})
    completed.write_text(
        json.dumps({"file_id": V3_FILE, "changes": updates, "result": result}, indent=2) + "\n"
    )
    print("Applied recoverable contour/UV correction; visual capture and native bake required")


if __name__ == "__main__":
    main()
