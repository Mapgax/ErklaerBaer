from __future__ import annotations

import fcntl
import json
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .errors import BudgetExceeded


class BudgetLedger:
    """Reserve externally billable work before sending it to a provider."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @staticmethod
    def _month_key(now: datetime | None = None) -> str:
        value = now or datetime.now(UTC)
        return value.strftime("%Y-%m")

    def load(self) -> dict[str, object]:
        if not self.path.exists():
            return {"schema_version": 1, "months": {}}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or not isinstance(payload.get("months"), dict):
            raise ValueError("Invalid usage ledger")
        return payload

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix(".lock").open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def initialize_production_task(self) -> None:
        """One allowance for this upgrade; setdefault never renews it on resume."""
        with self.locked():
            payload = self.load()
            payload.setdefault(
                "production_v2",
                {
                    "limits": {
                        "bfl_credits_reserved": 300,
                        "bfl_requests": 15,
                        "llm_calls": 24,
                        "tts_characters": 30000,
                    },
                    "used": {},
                    "actual": {},
                    "baseline_months": json.loads(json.dumps(payload["months"])),
                },
            )
            self._save(payload)

    def reserve(self, counter: str, amount: int, limit: int, *, dry_run: bool) -> int:
        if amount < 0 or limit < 0:
            raise ValueError("Budget values must be non-negative")
        with self.locked():
            payload = self.load()
            months = payload["months"]
            month = months.setdefault(self._month_key(), {})
            if not isinstance(month, dict):
                raise ValueError("Invalid monthly usage entry")
            projected = int(month.get(counter, 0)) + amount
            if projected > limit:
                raise BudgetExceeded(
                    f"Monthly {counter} budget exceeded: {projected} requested, limit {limit}"
                )
            task = payload.get("production_v2")
            additions = {counter: amount}
            if counter == "bfl_credits_reserved" and amount:
                additions["bfl_requests"] = 1
            if task:
                for name, value in additions.items():
                    if name not in task["limits"]:
                        continue
                    total = task["used"].get(name, 0) + value
                    if total > task["limits"][name]:
                        raise BudgetExceeded(f"Production v2 {name} allowance exhausted")
                for name, value in additions.items():
                    if name in task["limits"]:
                        task["used"][name] = task["used"].get(name, 0) + value
            if not dry_run:
                month[counter] = projected
                self._save(payload)
            return projected

    def record_actual(self, request_id: str, counter: str, amount: float) -> None:
        if amount < 0:
            raise ValueError("Actual charge must be non-negative")
        with self.locked():
            payload = self.load()
            actual = payload.setdefault("actual_charges", {})
            charge = {"counter": counter, "amount": amount}
            if request_id in actual and actual[request_id] != charge:
                raise ValueError("Conflicting actual charge for request")
            actual[request_id] = charge
            self._save(payload)

    def current(self, counter: str) -> int:
        payload = self.load()
        months = payload["months"]
        assert isinstance(months, dict)
        month = months.get(self._month_key(), {})
        return int(month.get(counter, 0)) if isinstance(month, dict) else 0

    def _save(self, payload: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            temporary_path = Path(handle.name)
        temporary_path.replace(self.path)
