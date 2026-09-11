from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .errors import ConfigurationError
from .models import Language

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.toml"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


def load_dotenv(path: Path = DEFAULT_ENV_PATH) -> None:
    """Load a small, strict .env file without printing or overwriting values."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(f"Invalid .env line in {path.name}")
        name, value = line.split("=", 1)
        name = name.strip()
        if not name.replace("_", "").isalnum() or not name[0].isalpha():
            raise ConfigurationError(f"Invalid environment variable name in {path.name}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


@dataclass(frozen=True)
class Settings:
    raw: dict[str, Any]
    project_root: Path = PROJECT_ROOT

    def section(self, name: str) -> dict[str, Any]:
        value = self.raw.get(name)
        if not isinstance(value, dict):
            raise ConfigurationError(f"Missing config section [{name}]")
        return value

    @property
    def dry_run(self) -> bool:
        return os.getenv("DRY_RUN", "true").strip().lower() not in {"0", "false", "no"}

    @property
    def language_mode(self) -> str:
        mode = str(self.section("project").get("language_mode", "alternating"))
        if mode not in {"alternating", "both"}:
            raise ConfigurationError("language_mode must be alternating or both")
        return mode

    def language_for_date(self, value: date) -> Language:
        project = self.section("project")
        if project.get("date_parity_algorithm") != "days_since_epoch_modulo_2":
            raise ConfigurationError("Unsupported date parity algorithm")
        try:
            epoch = date.fromisoformat(str(project["date_epoch"]))
        except (KeyError, ValueError) as exc:
            raise ConfigurationError("date_epoch must be an ISO calendar date") from exc
        ordinal = (value - epoch).days
        key = "even_ordinal" if ordinal % 2 == 0 else "odd_ordinal"
        return Language(self.section("languages")[key])

    def voice_for(self, language: Language) -> str:
        return str(self.section("voices")[language.value])

    def speaking_rate_for(self, language: Language) -> float:
        return float(self.section("speaking_rates")[language.value])

    def required_env(self, *names: str) -> dict[str, str]:
        result = {name: os.getenv(name, "").strip() for name in names}
        missing = [name for name, value in result.items() if not value]
        if missing:
            raise ConfigurationError("Missing environment values: " + ", ".join(missing))
        return result


def load_settings(path: Path = DEFAULT_CONFIG_PATH, env_path: Path = DEFAULT_ENV_PATH) -> Settings:
    load_dotenv(env_path)
    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Configuration not found: {path}") from exc
    settings = Settings(raw=raw, project_root=path.resolve().parents[1])
    _validate_settings(settings)
    return settings


def _validate_settings(settings: Settings) -> None:
    _ = settings.language_mode
    settings.language_for_date(date(2026, 9, 4))
    for language in Language:
        if not settings.voice_for(language):
            raise ConfigurationError(f"Missing voice for {language.value}")
        if not 0.50 <= settings.speaking_rate_for(language) <= 1.10:
            raise ConfigurationError(
                f"TTS speaking rate for {language.value} must stay between 0.50 and 1.10"
            )
    sources = settings.section("sources")
    for name in ("experiments_url", "schedule_url"):
        parsed = urlparse(str(sources.get(name, "")))
        if parsed.scheme != "https" or not parsed.netloc:
            raise ConfigurationError(f"{name} must use HTTPS")
    content = settings.section("content")
    minimum = float(content["target_min_seconds"])
    target_maximum = float(content["target_max_seconds"])
    hard_maximum = float(content["hard_max_seconds"])
    if not 0 < minimum <= target_maximum <= hard_maximum <= 300:
        raise ConfigurationError("Invalid duration thresholds")
    render = settings.section("render")
    if (int(render["width"]), int(render["height"]), int(render["fps"])) != (1920, 1080, 30):
        raise ConfigurationError("Production render must be 1920x1080 at 30 fps")
    if int(render["audio_sample_rate"]) != 48_000:
        raise ConfigurationError("Production audio must use 48 kHz")
    tts = settings.section("tts")
    if tts.get("provider") != "chirp3-hd":
        raise ConfigurationError("Only the reviewed chirp3-hd provider is supported")
    if not 0.2 <= float(tts["scene_tail_seconds"]) <= 1.0:
        raise ConfigurationError("TTS scene_tail_seconds must stay between 0.2 and 1.0")
    youtube = settings.section("youtube")
    if youtube.get("upload_privacy") != "private":
        raise ConfigurationError("Uploads must start private")
    if youtube.get("made_for_kids") is not True:
        raise ConfigurationError("Made-for-kids designation cannot be disabled")
    if youtube.get("notify_subscribers") is not False:
        raise ConfigurationError("Subscriber notifications must remain disabled")
    budgets = settings.section("budgets")
    for name in (
        "monthly_tts_characters",
        "monthly_llm_calls",
        "max_generation_attempts",
        "max_videos_per_run",
    ):
        if int(budgets[name]) <= 0:
            raise ConfigurationError(f"{name} must be positive")
    asset_design = settings.section("asset_design")
    if asset_design.get("model") != "flux-2-pro":
        raise ConfigurationError("Mascot design must use the pinned flux-2-pro model")
    endpoint = urlparse(str(asset_design.get("endpoint", "")))
    if endpoint.scheme != "https" or endpoint.hostname != "api.eu.bfl.ai":
        raise ConfigurationError("Mascot design must use the configured BFL EU endpoint")
    width = int(asset_design["width"])
    height = int(asset_design["height"])
    if width < 512 or height < 512 or width * height > 4_000_000:
        raise ConfigurationError("Invalid BFL mascot concept dimensions")
    reserved = int(asset_design["reserved_credits_per_image"])
    credit_limit = int(asset_design["monthly_credit_limit"])
    if not 0 < reserved <= credit_limit <= 1000:
        raise ConfigurationError("Invalid BFL local credit guard")
    if int(asset_design["max_images_per_run"]) != 1:
        raise ConfigurationError("BFL mascot concepts must be generated one at a time")
