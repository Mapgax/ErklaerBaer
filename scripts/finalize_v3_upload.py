"""Attach captions, thumbnail and playlist to an already uploaded private cut.

Separated from the upload because YouTube rejects caption writes until it has finished
processing the file. Safe to re-run: every step checks what the channel already holds.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from erklaerbaer.config import load_settings
from erklaerbaer.media import validate_media
from erklaerbaer.models import Storyboard
from erklaerbaer.youtube import YouTubeClient


def wait_for_processing(client: YouTubeClient, video_id: str, timeout: float) -> str:
    deadline = time.monotonic() + timeout
    while True:
        response = (
            client.service.videos().list(part="status,processingDetails", id=video_id).execute()
        )
        items = response.get("items", [])
        if not items:
            raise SystemExit(f"Video {video_id} is not visible on this account")
        status = items[0].get("processingDetails", {}).get("processingStatus", "unknown")
        print(f"processing status: {status}", flush=True)
        if status in {"succeeded", "terminated", "failed"} or time.monotonic() > deadline:
            return status
        time.sleep(20)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--cut", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=900.0)
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root

    manifest = json.loads((args.cut / "manifest.json").read_text())
    episode = manifest["episode_build"]
    board = Storyboard.model_validate_json(
        (root / "artifacts/review-v3/guitar" / episode / "storyboard.json").read_text()
    )
    client = YouTubeClient(settings)
    status = wait_for_processing(client, args.video_id, args.timeout)
    if status != "succeeded":
        raise SystemExit(f"Refusing to attach assets: processing status is {status}")

    client._ensure_post_upload_assets(
        args.video_id,
        board,
        args.cut / "captions.srt",
        args.cut / "thumbnail.jpg",
    )
    privacy = client.privacy_status(args.video_id)
    report = validate_media(args.cut / "full-review.mp4", settings)
    captions = client.service.captions().list(part="snippet", videoId=args.video_id).execute()
    evidence = {
        "video_id": args.video_id,
        "url": f"https://youtu.be/{args.video_id}",
        "privacy": privacy,
        "date": datetime.now(UTC).date().isoformat(),
        "intro_build": args.cut.name,
        "episode_build": episode,
        "intro_seconds": manifest["duration"],
        "duration_seconds_local": report.probe.duration_seconds,
        "integrated_lufs": report.loudness.integrated_lufs,
        "true_peak_dbfs": report.loudness.true_peak_dbfs,
        "caption_tracks": [
            {
                "language": item["snippet"]["language"],
                "name": item["snippet"]["name"],
                "status": item["snippet"].get("status"),
            }
            for item in captions.get("items", [])
        ],
        "made_for_kids": True,
        "notifications": False,
        "custom_thumbnail_error": client.thumbnail_error,
        "supersedes": "z_1Fx6L3N_Q",
        "owner_creative_approved": False,
    }
    out = root / "artifacts/review-v3/youtube-private-upload-v2.json"
    out.write_text(json.dumps(evidence, indent=1) + "\n")
    print(json.dumps(evidence, indent=1))
    if privacy != "private":
        raise SystemExit(f"Uploaded video is {privacy}, expected private")


if __name__ == "__main__":
    main()
