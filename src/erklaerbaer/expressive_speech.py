"""Bounded Gemini 2.5 Flash TTS with conservative token reservations and PCM reuse.

Only public script text and delivery instructions leave the machine. Billing estimates
are explicitly separate from provider-reported actual charges (unavailable in this API).
"""

from __future__ import annotations

import math

from .audio import _decode_wav
from .budgets import BudgetLedger
from .config import Settings
from .errors import BudgetExceeded, ExternalServiceError
from .speech_cache import SpeechCache, digest_json

MODEL = "gemini-2.5-flash-tts"
# Published model maxima, not a duration guessed from text length.
INPUT_TOKENS = 8192
AUDIO_TOKENS = 16384
REQUEST_MICRO_USD = 167936  # 8192 * $0.50/M + 16384 * $10/M
TRIAL_REQUESTS = 4
# Below this, a line is short enough that a model may treat it as a fragment to expand.
SHORT_LINE_CHARACTERS = 60
# One trial and one benchmark got 20. The owner authorized a second episode on
# 2026-09-10 after comparing the reservation to the billed cost; see the
# authorizations entry in catalog/usage.json. The constant and the ledger must both
# allow a request, so raising one alone still cannot spend anything.
TASK_REQUESTS = 58  # does not renew on resume
PROFILES = {
    "warm": "Warm, calm adult female science narrator. Natural curiosity, clear gentle emphasis. ",
    "curious": "A gentle friendly bear asking a sincere question. Warm natural adult voice. ",
    "satisfied": "Warm, calm adult female narrator with quiet satisfaction at understanding. ",
}


def speech_identity(segment, language: str, sample_rate: int = 48000) -> dict:
    profile = PROFILES[segment.delivery]
    locale = "Netherlands Dutch" if language == "nl-NL" else "standard German"
    instructions = (
        profile + f"Speak {locale} at about 112 words per minute, with deliberate "
        "short pauses between ideas. No exaggerated acting, caricature, music or "
        "sound effects. Speak only the supplied text."
    )
    # A very short line reads as a fragment, and the model then repeats it several times
    # over with long pauses between. Measured on a 20-character recap line that came back
    # spoken six times. The bear instruction has always said this; the narrator now does too.
    if len(segment.text) < SHORT_LINE_CHARACTERS:
        instructions += " Read the sentence exactly once, then stop."
    if segment.speaker == "bear":
        instructions = (
            "Spreek Nederlands met een warme, ontspannen volwassen mannenstem. "
            "Alsof je rustig en vriendelijk met iemand naast je praat, met een kleine glimlach. "
            "Natuurlijke nieuwsgierigheid, zachte nadruk, normaal gesprekstempo. "
            "Lees uitsluitend de opgegeven tekst, precies één keer."
            if language == "nl-NL"
            else "Speak standard German in a warm, relaxed adult male voice, conversationally, "
            "with a slight smile and gentle curiosity. Read only the supplied text, exactly once."
        )
    return {
        "cache_version": 2,
        "provider": "google-cloud-tts",
        "model": MODEL,
        "voice": "Achird" if segment.speaker == "bear" else "Sulafat",
        "speaker": segment.speaker,
        "instructions": instructions,
        "text": segment.text,
        "language": language,
        "encoding": "LINEAR16",
        "sample_rate": sample_rate,
    }


def reserve_request(
    ledger: BudgetLedger,
    key: str,
    characters: int,
    monthly_limit: int,
    *,
    phase: str,
    dry_run: bool = False,
) -> None:
    if phase not in {"trial", "benchmark"}:
        raise ValueError("Only bounded trial and guitar benchmark are authorized")
    with ledger.locked():
        payload = ledger.load()  # Always read current allowance immediately before paid work.
        task = payload.get("production_v2")
        if not task:
            raise BudgetExceeded("Existing production allowance is required")
        gemini = payload.setdefault(
            "gemini_v3",
            {
                "max_requests": TASK_REQUESTS,
                "max_trial_requests": TRIAL_REQUESTS,
                "max_reserved_micro_usd": TASK_REQUESTS * REQUEST_MICRO_USD,
                "reservations": {},
                "measured_estimates": {},
            },
        )
        reservations = gemini["reservations"]
        if key in reservations:
            raise ExternalServiceError("Existing Gemini reservation: recover; never resubmit")
        if (
            len(reservations) >= min(TASK_REQUESTS, gemini["max_requests"])
            or sum(v["micro_usd"] for v in reservations.values()) + REQUEST_MICRO_USD
            > min(TASK_REQUESTS * REQUEST_MICRO_USD, gemini["max_reserved_micro_usd"])
            or (
                phase == "trial"
                and sum(v["phase"] == "trial" for v in reservations.values())
                >= min(TRIAL_REQUESTS, gemini["max_trial_requests"])
            )
        ):
            raise BudgetExceeded("Finite Gemini trial/benchmark reservation exhausted")
        month = payload["months"].setdefault(ledger._month_key(), {})
        if month.get("tts_characters", 0) + characters > monthly_limit:
            raise BudgetExceeded("Monthly TTS character limit exceeded")
        used = task["used"].get("tts_characters", 0)
        if used + characters > task["limits"]["tts_characters"]:
            raise BudgetExceeded("Persistent TTS character allowance exhausted")
        reservations[key] = {
            "phase": phase,
            "input_tokens": INPUT_TOKENS,
            "audio_tokens": AUDIO_TOKENS,
            "micro_usd": REQUEST_MICRO_USD,
            "characters_including_prompt": characters,
        }
        task["used"]["tts_characters"] = used + characters
        month["tts_characters"] = month.get("tts_characters", 0) + characters
        if not dry_run:
            ledger._save(payload)


def synthesize_segment(
    settings: Settings, identity: dict, *, phase="benchmark", cache_only=False, retry_rejected=False
) -> tuple[bytes, bool]:
    cache = SpeechCache(settings.project_root / "build/audio-cache")
    content = cache.read(identity)
    if content is not None:
        return content, True
    if cache_only or settings.dry_run:
        raise ExternalServiceError("Cache-only/dry run: no expressive TTS call")
    if identity["model"] != MODEL or any(
        len(identity[k].encode()) > 4000 for k in ("text", "instructions")
    ):
        raise ValueError("Unsupported model or input exceeds documented byte bound")
    settings.required_env("GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS")
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    key = digest_json(identity)
    ledger = BudgetLedger(settings.project_root / "catalog/usage.json")
    # Claim cache first. Reserve failures can be safely retried after removal of this claim;
    # once the network request starts, only recovery can remove the pending marker.
    reservation_key = key
    if retry_rejected and cache.paths(key)[2].exists():
        state = ledger.load().get("gemini_v3", {}).get("reservations", {})
        previous = state.get(key, {})
        # A call that failed after it was sent may or may not have been billed, so the
        # original reservation is kept and the retry gets a reservation of its own. One
        # retry only, and only for a failure the journal actually recorded.
        recorded = str(previous.get("outcome", ""))
        recoverable = recorded == "rejected-service-disabled" or recorded.startswith("failed-")
        if not recoverable or key + ":retry-1" in state:
            raise ExternalServiceError("Only one explicit retry of a recorded failure")
        reservation_key = key + ":retry-1"
        cache.paths(key)[2].unlink()
    cache.begin(identity)
    try:
        reserve_request(
            ledger,
            reservation_key,
            len(identity["text"]) + len(identity["instructions"]),
            int(settings.section("budgets")["monthly_tts_characters"]),
            phase=phase,
        )
    except Exception:
        cache.paths(key)[2].unlink(missing_ok=True)
        raise
    try:
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(
                text=identity["text"], prompt=identity["instructions"]
            ),
            voice=texttospeech.VoiceSelectionParams(
                language_code=identity["language"], name=identity["voice"], model_name=MODEL
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=identity["sample_rate"],
            ),
            retry=None,
            timeout=90,
        )
        samples, rate = _decode_wav(response.audio_content)
        duration = len(samples) / rate
        cache.save(identity, response.audio_content, duration)
        with ledger.locked():
            payload = ledger.load()
            audio_tokens = math.ceil(duration * 25)
            payload["gemini_v3"]["measured_estimates"][key] = {
                "seconds": duration,
                "audio_tokens_estimate": audio_tokens,
                "input_tokens_actual": None,
                "provider_actual_usd": None,
                "audio_usd_estimate": audio_tokens * 10 / 1_000_000,
                "input_usd_upper_bound": INPUT_TOKENS * 0.5 / 1_000_000,
            }
            ledger._save(payload)
        if audio_tokens > AUDIO_TOKENS:
            raise ExternalServiceError(
                "Audio exceeded documented maximum; reconcile before more calls"
            )
        return response.audio_content, False
    except Exception as exc:
        disabled = type(exc).__name__ == "PermissionDenied" and "SERVICE_DISABLED" in str(exc)
        # Record every failure, so a later retry is a reconciliation and not a guess.
        with ledger.locked():
            payload = ledger.load()
            entry = payload["gemini_v3"]["reservations"].get(reservation_key)
            if entry is not None and "outcome" not in entry:
                entry["outcome"] = (
                    "rejected-service-disabled" if disabled else f"failed-{type(exc).__name__}"
                )
                ledger._save(payload)
        raise ExternalServiceError(
            f"Gemini TTS failed: {type(exc).__name__}; reservation retained"
        ) from exc
