"""Upload one finished private review cut and verify what the channel actually holds.

Private only. The marker carries the episode build, so re-running recovers this exact cut
instead of matching an earlier render of the same script.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from erklaerbaer.config import load_settings
from erklaerbaer.cuts import load_cut, write_record
from erklaerbaer.media import validate_media
from erklaerbaer.youtube import YouTubeClient, content_marker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cut", type=Path, required=True, help="intro build folder")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    settings = load_settings()
    root = settings.project_root
    cut = load_cut(root, args.cut)
    report = validate_media(cut.video, settings)
    if not (report.probe.has_h264 and report.probe.has_aac):
        raise SystemExit("Refusing to upload: media validation failed")

    print("marker      ", content_marker(cut.board, cut.marker_build))
    print("video       ", cut.video, f"{cut.video.stat().st_size / 1e6:.1f} MB")
    print("thumbnail   ", cut.thumbnail)
    print("duration    ", report.probe.duration_seconds)
    print("loudness    ", report.loudness)
    if args.dry_run:
        print("dry run: nothing was sent")
        return

    client = YouTubeClient(settings)
    result = client.upload_private(
        cut.board, cut.video, cut.captions, cut.thumbnail, build=cut.marker_build
    )
    privacy = client.privacy_status(result.youtube_id)
    write_record(
        cut.record_path(root),
        {
            "video_id": result.youtube_id,
            "url": f"https://youtu.be/{result.youtube_id}",
            "privacy": privacy,
            "recovered_existing": result.recovered,
            "date": datetime.now(UTC).date().isoformat(),
            "intro_build": cut.folder.name,
            "episode_build": cut.episode_build,
            "intro_seconds": cut.manifest["duration"],
            "duration_seconds_local": report.probe.duration_seconds,
            "integrated_lufs": report.loudness.integrated_lufs,
            "captions_uploaded": cut.board.language.value,
            "made_for_kids": bool(settings.section("youtube")["made_for_kids"]),
            "notifications": False,
            "custom_thumbnail_error": client.thumbnail_error,
            "owner_creative_approved": False,
        },
    )
    if privacy != "private":
        raise SystemExit(f"Uploaded video is {privacy}, expected private")


if __name__ == "__main__":
    main()
