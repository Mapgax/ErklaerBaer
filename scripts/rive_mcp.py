"""Scoped official desktop Rive MCP client. No remote endpoint or model calls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

ENDPOINT = "http://127.0.0.1:9791/mcp"


def rpc(method: str, params: dict | None = None, *, notification: bool = False):
    body = {"jsonrpc": "2.0", "method": method}
    if not notification:
        body["id"] = 1
    if params is not None:
        body["params"] = params
    request = Request(
        ENDPOINT,
        json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    with urlopen(request, timeout=60) as response:
        content = response.read()
    result = json.loads(content) if content else {}
    if "error" in result:
        raise RuntimeError(result["error"])
    return result.get("result", {})


def connect():
    rpc(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ErklaerBaer-authoring", "version": "0.1"},
        },
    )
    rpc("notifications/initialized", notification=True)


def call(name: str, arguments: dict):
    return rpc("tools/call", {"name": name, "arguments": arguments})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tool")
    parser.add_argument("arguments", help="Local JSON argument file")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    connect()
    result = call(args.tool, json.loads(Path(args.arguments).read_text()))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        # Never print inline file bytes.
        print(args.output)
    else:
        print(json.dumps(result, indent=2))
