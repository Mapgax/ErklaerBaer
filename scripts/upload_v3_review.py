"""Upload one finished private review cut and verify what the channel actually holds.

Private only. The marker carries the episode build, so re-running recovers this exact cut
instead of matching an earlier render of the same script.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from erklaerbaer.config import load_settings
from erklaerbaer.media import validate_media
from erklaerbaer.models import Storyboard
from erklaerbaer.youtube import YouTubeClient, content_marker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cut", type=Path, required=True, help="intro build folder")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root

    manifest = json.loads((args.cut / "manifest.json").read_text())
    episode = manifest["episode_build"]
    # The cut names its episode; the episode may live under any template's folder.
    folders = list((root / "artifacts/review-v3").glob(f"*/{episode}"))
    if len(folders) != 1:
        raise SystemExit(f"Expected one episode folder for {episode}, found {folders}")
    board = Storyboard.model_validate_json((folders[0] / "storyboard.json").read_text())
    video = args.cut / "full-review.mp4"
    report = validate_media(video, settings)
    if not (report.probe.has_h264 and report.probe.has_aac):
        raise SystemExit("Refusing to upload: media validation failed")

    # The cut is what gets uploaded: two cuts of one episode, say with and without an
    # outro, must not share an identity or a re-run recovers the wrong video.
    cut_id = f"{episode}|{args.cut.name}"
    marker = content_marker(board, cut_id)
    print("marker      ", marker)
    print("video       ", video, f"{video.stat().st_size / 1e6:.1f} MB")
    print("duration    ", report.probe.duration_seconds)
    print("loudness    ", report.loudness)
    if args.dry_run:
        print("dry run: nothing was sent")
        return

    client = YouTubeClient(settings)
    result = client.upload_private(
        board,
        video,
        args.cut / "captions.srt",
        args.cut / "thumbnail.jpg",
        build=cut_id,
    )
    privacy = client.privacy_status(result.youtube_id)
    evidence = {
        "video_id": result.youtube_id,
        "url": f"https://youtu.be/{result.youtube_id}",
        "privacy": privacy,
        "recovered_existing": result.recovered,
        "date": datetime.now(UTC).date().isoformat(),
        "intro_build": args.cut.name,
        "episode_build": episode,
        "intro_seconds": manifest["duration"],
        "duration_seconds_local": report.probe.duration_seconds,
        "integrated_lufs": report.loudness.integrated_lufs,
        "captions_uploaded": board.language.value,
        "made_for_kids": bool(settings.section("youtube")["made_for_kids"]),
        "notifications": False,
        "custom_thumbnail_error": client.thumbnail_error,
        "owner_creative_approved": False,
    }
    out = root / "artifacts/review-v3/youtube-private-upload-v2.json"
    out.write_text(json.dumps(evidence, indent=1) + "\n")
    print(json.dumps(evidence, indent=1))
    if privacy != "private":
        raise SystemExit(f"Uploaded video is {privacy}, expected private")


if __name__ == "__main__":
    main()
