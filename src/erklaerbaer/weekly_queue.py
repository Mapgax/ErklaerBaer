"""Private weekly selection; locked claims, atomic state, no scheduler or paid calls.

Favorite observations are separate from public topic content. A missing/stale feed
never falls through to a public-topic selection. Running claims are not reassigned
on a clock timeout: explicit failure/retry is needed to avoid duplicate spending.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import random
import re
import secrets
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FavoriteSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: int = Field(ge=1, le=1)
    topic_ids: list[str] = Field(max_length=10000)
    revision: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("topic_ids")
    @classmethod
    def valid_ids(cls, values):
        if len(set(values)) != len(values) or any(
            not re.fullmatch(r"[a-z0-9-]+", v) for v in values
        ):
            raise ValueError("Invalid/duplicate favorite IDs")
        if values != sorted(values):
            raise ValueError("Feed IDs must be canonical sorted IDs")
        return values

    def verify(self):
        canonical = json.dumps(self.topic_ids, separators=(",", ":")).encode()
        if hashlib.sha256(canonical).hexdigest() != self.revision:
            raise ValueError("Favorite snapshot revision mismatch")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Favorite feed redirects are forbidden; credential stays on its origin")


def fetch_favorites(url: str, token: str) -> dict:
    parts = urlparse(url)
    if parts.scheme != "https" or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Feed requires HTTPS without URL credentials/query/fragment")
    if parts.path != "/api/production-favorites" or not token.strip():
        raise ValueError("Dedicated favorites feed and read-only token required")
    request = Request(
        url, headers={"X-Erklaerbaer-Read-Token": token, "Accept": "application/json"}
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            raw = response.read(200001)
            if len(raw) > 200000:
                raise ValueError("Favorite feed too large")
            if "no-store" not in response.headers.get("Cache-Control", ""):
                raise ValueError("Favorite feed must prohibit caching")
    except Exception as exc:
        raise ValueError(f"Favorite feed unavailable ({type(exc).__name__})") from None
    snapshot = FavoriteSnapshot.model_validate_json(raw)
    snapshot.verify()
    return {"snapshot": snapshot.model_dump(), "fetched_at": datetime.now(UTC).isoformat()}


class WeeklyQueue:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.path.with_suffix(".lock").open("a") as handle:
            os.chmod(handle.name, 0o600)
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield self.load()
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def load(self):
        if not self.path.exists():
            return {
                "schema_version": 1,
                "observations": {},
                "active_favorites": [],
                "slots": {},
                "last_language": "nl-NL",
                "activation": "disabled",
                "cadence": {"day": "Monday", "hour": 9, "timezone": "Europe/Berlin"},
            }
        data = json.loads(self.path.read_text())
        if data.get("schema_version") != 1 or not isinstance(data.get("slots"), dict):
            raise ValueError("Invalid private queue state")
        return data

    def save(self, data):
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w") as handle:
            os.chmod(temporary, 0o600)
            json.dump(data, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(self.path)

    @staticmethod
    def snapshot(envelope, now):
        if not isinstance(envelope, dict) or set(envelope) != {"snapshot", "fetched_at"}:
            raise ValueError("A current favorite snapshot is required")
        fetched = datetime.fromisoformat(envelope["fetched_at"])
        if (
            fetched.tzinfo is None
            or now - fetched > timedelta(hours=24)
            or fetched - now > timedelta(minutes=5)
        ):
            raise ValueError("Stale/invalid favorite fetch time blocks selection")
        snapshot = FavoriteSnapshot.model_validate(envelope["snapshot"])
        snapshot.verify()
        return snapshot

    def select(self, slot_id, public_topics, accepted_topics, envelope, *, now=None, seed=None):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", slot_id):
            raise ValueError("Slot ID must be an ISO date")
        date.fromisoformat(slot_id)
        now = now or datetime.now(UTC)
        with self.locked() as data:
            existing = data["slots"].get(slot_id)
            if existing:
                return existing  # retries retain topic, language and original snapshot even offline
            snapshot = self.snapshot(envelope, now)
            unknown = set(snapshot.topic_ids) - set(public_topics)
            if unknown:
                raise ValueError("Unknown favorite IDs: " + ", ".join(sorted(unknown)))
            # Only one unfinished slot may exist; no second selection can reserve spend.
            if any(s["state"] != "completed" for s in data["slots"].values()):
                raise ValueError("An unfinished slot must complete or explicitly retry first")
            current = set(snapshot.topic_ids)
            observed = data["observations"]
            newly_observed = current - set(observed)
            initial = not observed
            for topic in current:
                observed.setdefault(
                    topic, {"first_seen": now.isoformat(), "revision": snapshot.revision}
                )
            data["active_favorites"] = snapshot.topic_ids
            completed = {s["topic_id"] for s in data["slots"].values() if s["state"] == "completed"}
            covered = set(accepted_topics) | completed
            fresh = newly_observed - covered
            old = current - covered
            public = set(public_topics) - covered
            candidates = fresh or old or public
            if not candidates:
                self.save(data)
                raise ValueError("Coverage exhausted; explicit rebuild required")
            seed = secrets.randbits(64) if seed is None else seed
            topic = random.Random(seed).choice(sorted(candidates))
            reason = (
                ("initial-favorite" if initial else "new-favorite")
                if fresh
                else ("favorite-backlog" if old else "public-backlog")
            )
            selected = {
                "topic_id": topic,
                "language": "de-DE" if data["last_language"] == "nl-NL" else "nl-NL",
                "source_hash": public_topics[topic],
                "snapshot_revision": snapshot.revision,
                "selection_reason": reason,
                "random_seed": seed,
                "state": "selected",
                "selected_at": now.isoformat(),
                "build_hash": None,
            }
            data["slots"][slot_id] = selected
            self.save(data)
            return selected

    def claim(self, slot_id):
        with self.locked() as data:
            slot = data["slots"][slot_id]
            if slot["state"] not in {"selected", "failed"}:
                raise ValueError("Slot already claimed/completed; cannot spend twice")
            claim = secrets.token_hex(16)
            slot.update(state="running", claim=claim)
            self.save(data)
            return {**slot}

    def finish(self, slot_id, claim, *, build_hash=None, accepted=False, error=False):
        with self.locked() as data:
            slot = data["slots"][slot_id]
            if slot["state"] != "running" or not secrets.compare_digest(
                slot.get("claim", ""), claim
            ):
                raise ValueError("Only the active worker may finish this claim")
            if error:
                slot["state"] = "failed"
            elif not accepted or not build_hash or not re.fullmatch(r"[a-f0-9]{24}", build_hash):
                raise ValueError("Completion requires an exact accepted v3 build")
            else:
                slot.update(state="completed", build_hash=build_hash)
                data["last_language"] = slot["language"]
            slot.pop("claim", None)
            self.save(data)
