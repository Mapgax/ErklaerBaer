from __future__ import annotations

import importlib.util
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import imageio_ffmpeg

from .budgets import BudgetLedger
from .config import DEFAULT_ENV_PATH, Settings
from .renderer import available_font_paths
from .youtube import YouTubeClient


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def run_doctor(settings: Settings, *, online: bool) -> list[Check]:
    checks: list[Check] = []
    checks.append(_parity_check(settings))
    checks.append(_env_safety_check())
    checks.extend(_dependency_checks())
    checks.extend(_font_checks())
    checks.append(_encoder_check())
    checks.extend(_credential_presence_checks())
    checks.extend(_budget_checks(settings))
    if online and not settings.dry_run:
        checks.extend(_online_checks(settings))
    elif online:
        checks.append(Check("online APIs", "SKIP", "DRY_RUN=true prevents external checks"))
    return checks


def _parity_check(settings: Settings) -> Check:
    from datetime import date

    expected = {
        date(2026, 9, 4): "de-DE",
        date(2026, 9, 5): "nl-NL",
    }
    correct = all(
        settings.language_for_date(day).value == language for day, language in expected.items()
    )
    return Check(
        "language parity",
        "PASS" if correct else "FAIL",
        "2026-09-04 de-DE; 2026-09-05 nl-NL" if correct else "configured parity is wrong",
    )


def _env_safety_check() -> Check:
    if not DEFAULT_ENV_PATH.exists():
        return Check("local .env", "FAIL", ".env is missing")
    mode = DEFAULT_ENV_PATH.stat().st_mode & 0o777
    safe = mode & 0o077 == 0
    return Check(
        "local .env permissions",
        "PASS" if safe else "WARN",
        f"mode {mode:03o}" + ("" if safe else "; run chmod 600 .env"),
    )


def _dependency_checks() -> list[Check]:
    modules = {
        "anthropic": "Anthropic SDK",
        "googleapiclient": "Google API client",
        "google_auth_oauthlib": "Google OAuth",
        "google.cloud.texttospeech": "Google Cloud Text-to-Speech",
        "imageio": "imageio",
        "imageio_ffmpeg": "imageio-ffmpeg",
        "numpy": "NumPy",
        "PIL": "Pillow",
        "pydantic": "Pydantic",
    }
    return [
        Check(label, "PASS" if importlib.util.find_spec(module) else "FAIL", module)
        for module, label in modules.items()
    ]


def _font_checks() -> list[Check]:
    regular, bold = available_font_paths()
    return [
        Check("regular font", "PASS" if regular else "FAIL", str(regular or "not found")),
        Check("rounded bold font", "PASS" if bold else "FAIL", str(bold or "not found")),
    ]


def _encoder_check() -> Check:
    try:
        executable = Path(imageio_ffmpeg.get_ffmpeg_exe())
        exists = executable.is_file()
    except RuntimeError:
        executable = Path("not found")
        exists = False
    return Check("FFmpeg encoder", "PASS" if exists else "FAIL", str(executable))


def _credential_presence_checks() -> list[Check]:
    names = [
        "ANTHROPIC_API_KEY",
        "BFL_API_KEY",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
        "YOUTUBE_REFRESH_TOKEN",
        "YOUTUBE_CHANNEL_ID",
        "YOUTUBE_PLAYLIST_DE_ID",
        "YOUTUBE_PLAYLIST_NL_ID",
    ]
    result = [
        Check(
            name,
            "PASS" if os.getenv(name, "").strip() else "TODO",
            "set" if os.getenv(name, "").strip() else "not set",
        )
        for name in names
    ]
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if credentials_path:
        exists = Path(credentials_path).is_file()
        result.append(
            Check(
                "TTS credential file",
                "PASS" if exists else "FAIL",
                "found" if exists else "path not found",
            )
        )
    audited = os.getenv("YOUTUBE_API_AUDIT_COMPLETE", "false").lower() == "true"
    result.append(
        Check(
            "YouTube API audit",
            "PASS" if audited else "GATE",
            "confirmed" if audited else "required before automatic public release",
        )
    )
    return result


def _budget_checks(settings: Settings) -> list[Check]:
    ledger = BudgetLedger(settings.project_root / "catalog" / "usage.json")
    budgets = settings.section("budgets")
    return [
        Check(
            "monthly TTS characters",
            "PASS",
            f"{ledger.current('tts_characters')}/{int(budgets['monthly_tts_characters'])}",
        ),
        Check(
            "monthly LLM calls",
            "PASS",
            f"{ledger.current('llm_calls')}/{int(budgets['monthly_llm_calls'])}",
        ),
        Check(
            "BFL reserved credits",
            "PASS",
            f"{ledger.current('bfl_credits_reserved')}/"
            f"{int(settings.section('asset_design')['monthly_credit_limit'])}; "
            "one concept per command",
        ),
    ]


def _online_checks(settings: Settings) -> list[Check]:
    checks: list[Check] = []
    try:
        channel = YouTubeClient(settings).own_channel()
        configured = os.getenv("YOUTUBE_CHANNEL_ID", "")
        matches = str(channel["id"]) == configured
        checks.append(
            Check(
                "YouTube channel",
                "PASS" if matches else "FAIL",
                "OAuth channel matches YOUTUBE_CHANNEL_ID" if matches else "channel ID mismatch",
            )
        )
    except Exception as exc:  # provider libraries expose several unrelated exception types
        checks.append(Check("YouTube API", "FAIL", type(exc).__name__))
    try:
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()
        available = client.list_voices(language_code="de-DE")
        names = {voice.name for voice in available.voices}
        expected = settings.voice_for(
            settings.language_for_date(__import__("datetime").date(2026, 9, 4))
        )
        checks.append(
            Check(
                "Google TTS API",
                "PASS" if expected in names else "FAIL",
                "configured German voice available" if expected in names else "voice not returned",
            )
        )
    except Exception as exc:  # provider libraries expose several unrelated exception types
        checks.append(Check("Google TTS API", "FAIL", type(exc).__name__))
    return checks
