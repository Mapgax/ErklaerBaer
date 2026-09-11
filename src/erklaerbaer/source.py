from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pydantic import ValidationError

from .catalog import CatalogStore
from .config import Settings
from .errors import SourceError
from .models import ExperimentSnapshot, Language, VideoRequirement

JsonFetcher = Callable[[str], Any]


def fetch_public_json(url: str, *, timeout_seconds: float = 20.0) -> Any:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise SourceError("MINT source URLs must use HTTPS")
    request = Request(url, headers={"User-Agent": "ErklaerBaer/0.1"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            size = int(response.headers.get("Content-Length", "0") or 0)
            if size > 5_000_000:
                raise SourceError("MINT source response exceeds 5 MB")
            data = response.read(5_000_001)
    except (OSError, ValueError) as exc:
        raise SourceError(f"Could not fetch MINT source: {type(exc).__name__}") from exc
    if len(data) > 5_000_000:
        raise SourceError("MINT source response exceeds 5 MB")
    try:
        return json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError("MINT source did not return valid UTF-8 JSON") from exc


class MintSource:
    def __init__(self, settings: Settings, fetcher: JsonFetcher = fetch_public_json) -> None:
        self.settings = settings
        self.fetcher = fetcher

    def experiments(self) -> dict[str, ExperimentSnapshot]:
        url = str(self.settings.section("sources")["experiments_url"])
        payload = self.fetcher(url)
        records = payload.get("experiments", payload) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise SourceError("Experiment source must contain a list")
        result: dict[str, ExperimentSnapshot] = {}
        for raw in records:
            if not isinstance(raw, dict):
                raise SourceError("Experiment entries must be JSON objects")
            try:
                snapshot = ExperimentSnapshot.from_mint(raw)
            except ValidationError as exc:
                raise SourceError(f"Invalid experiment record: {exc.errors()[0]['msg']}") from exc
            if snapshot.id in result:
                raise SourceError(f"Duplicate experiment ID: {snapshot.id}")
            result[snapshot.id] = snapshot
        return result

    def schedule(self) -> dict[date, str]:
        url = str(self.settings.section("sources")["schedule_url"])
        payload = self.fetcher(url)
        raw_schedule = payload.get("schedule", payload) if isinstance(payload, dict) else payload
        result: dict[date, str] = {}
        if isinstance(raw_schedule, dict):
            entries = raw_schedule.items()
        elif isinstance(raw_schedule, list):
            entries = (
                (item.get("date"), item.get("experiment_id", item.get("experimentId")))
                for item in raw_schedule
                if isinstance(item, dict)
            )
        else:
            raise SourceError("Schedule source must contain an object or list")
        for raw_date, raw_id in entries:
            try:
                scheduled_date = date.fromisoformat(str(raw_date))
            except ValueError as exc:
                raise SourceError(f"Invalid schedule date: {raw_date}") from exc
            experiment_id = str(raw_id or "").strip()
            if not experiment_id:
                raise SourceError(f"Missing experiment ID for {scheduled_date}")
            result[scheduled_date] = experiment_id
        return result

    def discover(
        self,
        catalog: CatalogStore,
        *,
        start: date,
        days: int,
    ) -> list[VideoRequirement]:
        if not 1 <= days <= 90:
            raise ValueError("days must be between 1 and 90")
        experiments = self.experiments()
        schedule = self.schedule()
        requirements: list[VideoRequirement] = []
        seen: set[tuple[str, Language, str]] = set()

        for offset in range(days):
            scheduled_date = start + timedelta(days=offset)
            experiment_id = schedule.get(scheduled_date)
            if experiment_id is None:
                continue
            experiment = experiments.get(experiment_id)
            if experiment is None:
                raise SourceError(f"Schedule references unknown experiment: {experiment_id}")
            languages = (
                [Language.GERMAN, Language.DUTCH]
                if self.settings.language_mode == "both"
                else [self.settings.language_for_date(scheduled_date)]
            )
            for language in languages:
                key = (experiment.id, language, experiment.source_hash)
                if key in seen:
                    continue
                seen.add(key)
                requirements.append(
                    VideoRequirement(
                        date=scheduled_date,
                        experiment_id=experiment.id,
                        language=language,
                        source_hash=experiment.source_hash,
                        exists=catalog.find(*key) is not None,
                    )
                )
        return requirements
