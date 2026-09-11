"""Three finite Google samples; cached Chirp baselines incur no calls."""

import argparse
import json

from erklaerbaer.config import load_settings
from erklaerbaer.expressive_speech import speech_identity, synthesize_segment
from erklaerbaer.models import SpeechSegment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry-rejected", action="store_true")
    args = parser.parse_args()
    settings = load_settings()
    out = settings.project_root / "artifacts/review-v3/voices"
    out.mkdir(parents=True, exist_ok=True)
    samples = [
        (
            "nl-NL",
            "narrator",
            "warm",
            (
                "Het trillende elastiek trekt en duwt aan de plekken waar het op de doos steunt. "
                "Zo gaat ook de doos een beetje meetrillen."
            ),
        ),
        ("nl-NL", "bear", "curious", "Maar waar komt dat geluid vandaan?"),
        (
            "de-DE",
            "narrator",
            "warm",
            (
                "Die warme Luft in der Flasche drückt gegen die Münze. "
                "Wird der Druck groß genug, hebt sich die Münze kurz an."
            ),
        ),
    ]
    for language, role, delivery, text in samples:
        name = f"{language}-{role}"
        identity = speech_identity(
            SpeechSegment(segment_id=name.lower(), text=text, speaker=role, delivery=delivery),
            language,
        )
        content, reused = synthesize_segment(
            settings, identity, phase="trial", retry_rejected=args.retry_rejected
        )
        (out / f"gemini-{name}.wav").write_bytes(content)
        (out / f"gemini-{name}.json").write_text(
            json.dumps(identity, ensure_ascii=False, indent=2) + "\n"
        )
        print(name, "cached" if reused else "generated", flush=True)
    # Locate exact text in verified historical cache; no narration call for the baseline.
    for language, topic in [("nl-NL", "karton-gitarre"), ("de-DE", "springende-muenze")]:
        timing = json.loads(
            (
                settings.project_root / f"artifacts/review-v2/pilots/{topic}/narration.timing.json"
            ).read_text()
        )
        key = timing["segments"][4 if language == "nl-NL" else 0]["cache_key"]
        source = settings.project_root / f"build/audio-cache/{key[:2]}/{key}.wav"
        (out / f"chirp-{language}.wav").write_bytes(source.read_bytes())


if __name__ == "__main__":
    main()
