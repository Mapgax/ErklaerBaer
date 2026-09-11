"""Content-addressed PCM cache; uncertain submissions never silently retry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .errors import ExternalServiceError


def digest_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class SpeechCache:
    def __init__(self, root: Path):
        self.root = root

    def paths(self, key: str) -> tuple[Path, Path, Path]:
        folder = self.root / key[:2]
        return folder / f"{key}.wav", folder / f"{key}.json", folder / f"{key}.pending"

    def read(self, identity: dict) -> bytes | None:
        key = digest_json(identity)
        wav, metadata, _ = self.paths(key)
        if not metadata.exists():
            return None
        info = json.loads(metadata.read_text())
        if not wav.exists() or info["identity"] != identity:
            raise ExternalServiceError("Speech cache is incomplete; repair locally before TTS")
        data = wav.read_bytes()
        if hashlib.sha256(data).hexdigest() != info["sha256"]:
            raise ExternalServiceError("Speech cache checksum mismatch")
        return data

    def begin(self, identity: dict) -> None:
        _, _, pending = self.paths(digest_json(identity))
        pending.parent.mkdir(parents=True, exist_ok=True)
        try:
            with pending.open("x") as handle:
                json.dump(identity, handle, ensure_ascii=False)
        except FileExistsError as exc:
            raise ExternalServiceError(
                "Uncertain TTS submission: recover cached response or reconcile provider "
                "before authorizing another submission"
            ) from exc

    def save(self, identity: dict, content: bytes, duration: float) -> None:
        wav, metadata, pending = self.paths(digest_json(identity))
        temporary = wav.with_suffix(".tmp")
        temporary.write_bytes(content)
        temporary.replace(wav)
        temporary = metadata.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "identity": identity,
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "duration_seconds": duration,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        temporary.replace(metadata)
        pending.unlink(missing_ok=True)
