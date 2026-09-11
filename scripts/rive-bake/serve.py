"""Occasional local Rive bake bridge. Launch, then click Bake in a browser."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LIBRARY = ROOT / "assets/mascot/rig/v2"
ACTIONS = {
    "neutral": {"animation": "idle_loop", "duration": 4.0, "loop": True},
    "lift": {"animation": "lift_v2", "duration": 2.0, "loop": False},
    "explain": {"animation": "explain_v2", "duration": 2.0, "loop": False},
    "think": {"animation": "think_v2", "duration": 2.5, "loop": False},
    "surprise": {"animation": "surprise_v2", "duration": 1.5, "loop": False},
    "aha": {"animation": "aha_v2", "duration": 1.8, "loop": False},
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--riv", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--library", type=Path, default=LIBRARY)
    args = parser.parse_args()
    library = args.library.resolve()
    if not library.is_relative_to((ROOT / "assets").resolve()):
        raise ValueError("Bake output must stay under project assets")
    riv = args.riv.resolve()
    assert riv.is_file()
    token = secrets.token_urlsafe(24)
    controller = {
        "view_model": "ViewModel1",
        "property": "action",
        "values": dict(zip(ACTIONS, range(6), strict=True)),
    }
    config = {
        "artboard": "ErklaerBaer_Mascot",
        "state_machine": "State Machine 1",
        "controller": controller,
        "actions": ACTIONS,
        "token": token,
    }
    routes = {
        "/": (HERE / "index.html", "text/html"),
        "/runtime.mjs": (
            HERE / "node_modules/@rive-app/canvas-advanced/canvas_advanced.mjs",
            "text/javascript",
        ),
        "/rive.wasm": (
            HERE / "node_modules/@rive-app/canvas-advanced/rive.wasm",
            "application/wasm",
        ),
        "/mascot.riv": (riv, "application/octet-stream"),
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, data, status=200, mime="text/plain"):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def valid_host(self):
            return self.headers.get("Host") == f"127.0.0.1:{args.port}"

        def do_GET(self):
            if not self.valid_host():
                return self.respond(b"Invalid host", 403)
            if self.path == "/config.json":
                return self.respond(json.dumps(config).encode(), mime="application/json")
            if self.path not in routes:
                return self.respond(b"Not found", 404)
            path, mime = routes[self.path]
            self.respond(path.read_bytes(), mime=mime)

        def do_POST(self):
            if (
                not self.valid_host()
                or self.headers.get("X-Bake-Token") != token
                or self.headers.get("Origin") != f"http://127.0.0.1:{args.port}"
            ):
                return self.respond(b"Forbidden", 403)
            if self.path == "/complete":
                manifest = {
                    "schema_version": 2,
                    "artboard": config["artboard"],
                    "state_machine": config["state_machine"],
                    "controller": controller,
                    "dimensions": [600, 800],
                    "fps": 30,
                    "pivot": [0.5, 0.9],
                    "review_status": "provisional",
                    "owner_approved": False,
                    "runtime": {
                        "file": riv.name,
                        "sha256": hashlib.sha256(riv.read_bytes()).hexdigest(),
                    },
                    "actions": {},
                }
                for action, spec in ACTIONS.items():
                    count = round(spec["duration"] * 30) + (not spec["loop"])
                    frames = []
                    for i in range(count):
                        path = library / "frames" / action / f"{i:04}.png"
                        if not path.is_file():
                            return self.respond(b"Missing frames", 409)
                        frames.append(
                            {
                                "file": str(path.relative_to(library)),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            }
                        )
                    manifest["actions"][action] = {
                        **spec,
                        "behavior": "loop" if spec["loop"] else "play-once-hold-last",
                        "frames": frames,
                        "review_status": "provisional",
                    }
                (library / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
                return self.respond(b"Complete")
            match = re.fullmatch(r"/frames/([a-z]+)/([0-9]{4})\.png", self.path)
            if not match or match[1] not in ACTIONS:
                return self.respond(b"Invalid frame", 400)
            action, index = match[1], int(match[2])
            spec = ACTIONS[action]
            if index >= round(spec["duration"] * 30) + (not spec["loop"]):
                return self.respond(b"Invalid index", 400)
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size < 4_000_000:
                return self.respond(b"Invalid size", 413)
            data = self.rfile.read(size)
            try:
                with Image.open(io.BytesIO(data)) as im:
                    assert im.size == (600, 800) and im.mode == "RGBA"
                    im.verify()
            except Exception:
                return self.respond(b"Invalid PNG", 400)
            path = library / "frames" / action / f"{index:04}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            self.respond(b"OK")

    print(f"Open http://127.0.0.1:{args.port} and click Bake", flush=True)
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
