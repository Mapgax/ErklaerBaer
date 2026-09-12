"""One paid probe: does the pinned EU host serve FLUX 3 Video, and is a clip mattable?

Answers phase one of the clip plan. Draft quality on purpose, because the questions are
about the endpoint, the response shape and the background, not about the performance.

The host is pinned. If the EU host does not serve video this stops and says so; it never
falls back to another region on its own. Run with DRY_RUN=false on the invocation.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import imageio_ffmpeg
from PIL import Image

from erklaerbaer.budgets import BudgetLedger
from erklaerbaer.config import load_settings
from erklaerbaer.errors import BudgetExceeded, ExternalServiceError

# The paper ground every mascot asset is generated against; matting measures against it.
PAPER = (245, 240, 230)
KEYFRAME_LONG_EDGE = 1024

PROMPT_TEMPLATE = (
    "Keep the supplied frame exactly as it is drawn: the same flat children's "
    "illustration of a handmade paper and felt bear, the same colours, the same edges, the "
    "same even lighting. Animate only the character's own movement: {motion} "
    "Locked static camera, no camera movement, no zoom, no pan, no parallax. "
    "The background stays one perfectly flat uniform warm off-white field across the whole "
    "clip, with no wall, no floor, no horizon line, no cast shadow, no contact shadow, no "
    "vignette, no photographic studio lighting, no texture and no added scenery. "
    "Do not restyle, relight or re-render the character as a photograph or a 3D object. "
    "No extra characters, no text, no props appearing or disappearing."
)

AHA_MOTION = (
    "he looks up and raises his free paw in a small, calm, open-palmed gesture of "
    "understanding, then settles and holds still. He keeps hold of the magnifying glass "
    "in his other paw the whole time."
)


def _data_uri(path: Path) -> str:
    with Image.open(path) as source:
        image = source.convert("RGB")
    scale = KEYFRAME_LONG_EDGE / max(image.size)
    if scale < 1:
        image = image.resize(
            (round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS
        )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


class SubmissionRejected(ExternalServiceError):
    """The provider validated the body and refused it, so nothing was created or billed."""


def _json_request(url: str, api_key: str, *, method: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "accept": "application/json",
            "Content-Type": "application/json",
            "x-key": api_key,
        },
    )
    try:
        with urlopen(request, timeout=120.0) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read(4000).decode("utf-8", "replace")
        message = f"HTTP {exc.code} from {urlparse(url).path}: {detail}"
        if exc.code in {400, 422}:
            raise SubmissionRejected(message) from exc
        raise ExternalServiceError(message) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ExternalServiceError(f"BFL video request failed: {type(exc).__name__}") from exc


def _download(url: str) -> bytes:
    host = (urlparse(url).hostname or "").lower()
    if urlparse(url).scheme != "https" or not (host == "bfl.ai" or host.endswith(".bfl.ai")):
        raise ExternalServiceError(f"Result host {host} is outside the approved BFL domain")
    request = Request(url, method="GET", headers={"accept": "video/*"})
    with urlopen(request, timeout=300.0) as response:  # noqa: S310
        return response.read(200_000_001)


def _probe_media(path: Path) -> dict[str, Any]:
    """Read what came back with the same ffmpeg the pipeline already ships; no ffprobe."""
    result = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stderr
    dimensions = re.search(r"Video:.*?\b(\d{2,5})x(\d{2,5})\b", output)
    frame_rate = re.search(r"Video:.*?\b(\d+(?:\.\d+)?) fps\b", output)
    duration = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", output)
    seconds = (
        int(duration.group(1)) * 3600 + int(duration.group(2)) * 60 + float(duration.group(3))
        if duration
        else None
    )
    return {
        "duration_seconds": seconds,
        "width": int(dimensions.group(1)) if dimensions else None,
        "height": int(dimensions.group(2)) if dimensions else None,
        "fps": float(frame_rate.group(1)) if frame_rate else None,
        "video_codec_line": next(
            (line.strip() for line in output.splitlines() if "Video:" in line), None
        ),
        "audio_codec_line": next(
            (line.strip() for line in output.splitlines() if "Audio:" in line), None
        ),
    }


def _matte_report(video: Path, out_dir: Path, label: str) -> dict[str, Any]:
    """How flat is the background, and how far from the paper colour it drifts."""
    frames_dir = out_dir / f"frames-{label}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(frames_dir / "%03d.png")
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-v",
            "error",
            "-y",
            "-i",
            str(video),
            "-vf",
            "fps=2",
            pattern,
        ],
        check=True,
    )
    samples = sorted(frames_dir.glob("*.png"))
    report: list[dict[str, Any]] = []
    for frame in samples:
        with Image.open(frame) as source:
            image = source.convert("RGB")
        width, height = image.size
        band = 12
        edge_pixels = []
        for x in range(0, width, 4):
            edge_pixels.append(image.getpixel((x, band)))
            edge_pixels.append(image.getpixel((x, height - 1 - band)))
        for y in range(0, height, 4):
            edge_pixels.append(image.getpixel((band, y)))
            edge_pixels.append(image.getpixel((width - 1 - band, y)))
        deltas = [max(abs(p[i] - PAPER[i]) for i in range(3)) for p in edge_pixels]
        spread = [max(p[i] for p in edge_pixels) - min(p[i] for p in edge_pixels) for i in range(3)]
        report.append(
            {
                "frame": frame.name,
                "mean_delta_from_paper": round(sum(deltas) / len(deltas), 2),
                "max_delta_from_paper": max(deltas),
                "channel_spread": spread,
            }
        )
    return {
        "sampled_frames": len(report),
        "worst_mean_delta": max(r["mean_delta_from_paper"] for r in report) if report else None,
        "worst_max_delta": max(r["max_delta_from_paper"] for r in report) if report else None,
        "per_frame": report,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=Path, default=Path("assets/mascot/concepts/v1/neutral.png"))
    parser.add_argument("--end", type=Path, default=Path("assets/mascot/concepts/v2/aha.png"))
    parser.add_argument(
        "--single-keyframe",
        action="store_true",
        help="Anchor only the first frame and describe the movement, instead of pinning both ends",
    )
    parser.add_argument("--motion", default=AHA_MOTION, help="What the bear should do")
    parser.add_argument(
        "--quality",
        choices=("draft", "hd"),
        default="draft",
        help="draft is $0.06/s and reinterprets the artwork; hd is $0.17/s",
    )
    parser.add_argument(
        "--analyze",
        type=Path,
        help="Measure an already downloaded clip instead of generating a new one",
    )
    args = parser.parse_args()

    settings = load_settings()
    root = settings.project_root
    video = settings.section("video_design")
    out_dir = root / "build/v3/video-probe"
    out_dir.mkdir(parents=True, exist_ok=True)
    journal = out_dir / "journal.json"

    if args.analyze:
        clip = root / args.analyze
        media = _probe_media(clip)
        matte = _matte_report(clip, out_dir)
        print(
            json.dumps(
                {
                    "media": media,
                    "matte_summary": {
                        "sampled_frames": matte["sampled_frames"],
                        "worst_mean_delta": matte["worst_mean_delta"],
                        "worst_max_delta": matte["worst_max_delta"],
                    },
                },
                indent=2,
            )
        )
        existing = out_dir / "probe-report.json"
        report = json.loads(existing.read_text()) if existing.exists() else {}
        report.update({"media": media, "matte": matte, "bytes": clip.stat().st_size})
        existing.write_text(json.dumps(report, indent=2) + "\n")
        return

    if settings.dry_run:
        raise SystemExit("This probe spends money; run it with DRY_RUN=false on the invocation")

    api_key = settings.required_env("BFL_API_KEY")["BFL_API_KEY"]
    ledger = BudgetLedger(root / "catalog/usage.json")
    reserved = int(video["reserved_micro_usd_per_clip"])

    start = root / args.start
    end = root / args.end
    form = "single" if args.single_keyframe else "pair"
    keyframes: Any = _data_uri(start)
    if not args.single_keyframe:
        keyframes = [[0, _data_uri(start)], [int(video["duration_seconds"]), _data_uri(end)]]

    payload = {
        "mode": str(video["mode"]),
        "prompt": PROMPT_TEMPLATE.format(motion=args.motion),
        "keyframes": keyframes,
        "duration": int(video["duration_seconds"]),
        "aspect_ratio": str(video["aspect_ratio"]),
        "resolution": str(video["resolution"]),
        "generate_audio": bool(video["generate_audio"]),
        # No seed: the API rejects one for i2v, so a clip is reproducible only by caching it.
        "draft": args.quality == "draft",
    }

    endpoint = str(video["endpoint"])
    submitted: dict[str, Any] | None = None
    if journal.exists():
        saved = json.loads(journal.read_text())
        submitted = saved.get("submitted")
        if not submitted:
            raise SystemExit("Uncertain earlier submission: reconcile the journal before retrying")
        print("Recovering the earlier submission from the journal rather than resubmitting")
    if submitted is None:
        # Reserve immediately before the only call that can spend, and never on a recovery.
        try:
            projected = ledger.reserve(
                "bfl_video_micro_usd",
                reserved,
                int(video["monthly_micro_usd_limit"]),
                dry_run=False,
            )
        except BudgetExceeded as exc:
            raise SystemExit(f"Refusing to call the provider: {exc}") from exc
        print(f"Reserved {reserved} micro-USD; month now at {projected}")
        journal.write_text(json.dumps({"state": "submitting", "endpoint": endpoint}))
        print(f"POST {endpoint}")
        try:
            submitted = _json_request(endpoint, api_key, method="POST", payload=payload)
        except SubmissionRejected as exc:
            # A validation refusal is certain, not uncertain: nothing exists to reconcile.
            journal.unlink(missing_ok=True)
            raise SystemExit(
                f"Provider refused the request body, nothing was created:\n{exc}"
            ) from None
        journal.write_text(json.dumps({"state": "polling", "submitted": submitted}))

    polling_url = submitted.get("polling_url")
    request_id = submitted.get("id")
    print(f"Accepted: id={request_id}")
    if not isinstance(polling_url, str):
        raise SystemExit(f"No polling URL in the submission response: {submitted}")

    deadline = time.monotonic() + float(video["poll_timeout_seconds"])
    status_payload: dict[str, Any] = {}
    while time.monotonic() < deadline:
        time.sleep(float(video["poll_interval_seconds"]))
        status_payload = _json_request(polling_url, api_key, method="GET")
        status = str(status_payload.get("status", ""))
        print(f"  status={status}")
        if status == "Ready":
            break
        if status in {"Error", "Failed"}:
            raise SystemExit(f"Generation ended with status {status}: {status_payload}")
    else:
        raise SystemExit("Generation timed out")

    result = status_payload.get("result") or {}
    sample = result.get("sample") if isinstance(result, dict) else None
    if not isinstance(sample, str):
        raise SystemExit(f"Ready response has no result URL: {status_payload}")
    clip = out_dir / f"probe-{args.quality}-{form}.mp4"
    clip.write_bytes(_download(sample))
    journal.unlink(missing_ok=True)

    media = _probe_media(clip)
    matte = _matte_report(clip, out_dir, form)
    report = {
        "probed_at": datetime.now(UTC).isoformat(),
        "endpoint": endpoint,
        "request_id": request_id,
        "keyframe_form": form,
        "motion": args.motion,
        "draft": args.quality == "draft",
        "submitted_response": submitted,
        "result_host": urlparse(sample).hostname,
        "media": media,
        "matte": matte,
        "bytes": clip.stat().st_size,
        "reserved_micro_usd": reserved,
    }
    (out_dir / f"probe-report-{args.quality}-{form}.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "matte"}, indent=2))
    print(
        "matte: worst mean delta from paper "
        f"{matte['worst_mean_delta']}, worst max delta {matte['worst_max_delta']}"
    )


if __name__ == "__main__":
    main()
