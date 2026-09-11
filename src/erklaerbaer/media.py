from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg

from .config import Settings


@dataclass(frozen=True)
class MediaProbe:
    width: int
    height: int
    fps: float
    duration_seconds: float
    has_h264: bool
    has_aac: bool
    audio_sample_rate: int


@dataclass(frozen=True)
class LoudnessProbe:
    integrated_lufs: float
    true_peak_dbfs: float


@dataclass(frozen=True)
class MediaValidation:
    probe: MediaProbe
    loudness: LoudnessProbe
    warnings: tuple[str, ...]


def mux_and_normalize(silent_video: Path, narration: Path, output_path: Path) -> None:
    executable = imageio_ffmpeg.get_ffmpeg_exe()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(silent_video),
        "-i",
        str(narration),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=7,aresample=48000",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"FFmpeg mux failed with exit code {result.returncode}")


def probe_media(path: Path) -> MediaProbe:
    executable = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [executable, "-hide_banner", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stderr
    dimensions = re.search(r"Video:.*?\b(\d{2,5})x(\d{2,5})\b", output)
    frame_rate = re.search(r"Video:.*?\b(\d+(?:\.\d+)?) fps\b", output)
    audio_rate = re.search(r"Audio: aac.*?\b(\d+) Hz\b", output)
    duration = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if not dimensions or not frame_rate or not audio_rate or not duration:
        raise ValueError("Could not read required media metadata")
    seconds = int(duration.group(1)) * 3600 + int(duration.group(2)) * 60 + float(duration.group(3))
    return MediaProbe(
        width=int(dimensions.group(1)),
        height=int(dimensions.group(2)),
        fps=float(frame_rate.group(1)),
        duration_seconds=seconds,
        has_h264=bool(re.search(r"Video: h264\b", output)),
        has_aac=bool(re.search(r"Audio: aac\b", output)),
        audio_sample_rate=int(audio_rate.group(1)),
    )


def measure_loudness(path: Path) -> LoudnessProbe:
    executable = imageio_ffmpeg.get_ffmpeg_exe()
    result = subprocess.run(
        [
            executable,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-filter_complex",
            "ebur128=peak=true",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    integrated = re.findall(r"I:\s+(-?\d+(?:\.\d+)?) LUFS", result.stderr)
    peaks = re.findall(r"Peak:\s+(-?\d+(?:\.\d+)?) dBFS", result.stderr)
    if not integrated or not peaks:
        raise ValueError("Could not measure output loudness")
    return LoudnessProbe(
        integrated_lufs=float(integrated[-1]),
        true_peak_dbfs=float(peaks[-1]),
    )


def validate_media(path: Path, settings: Settings) -> MediaValidation:
    probe = probe_media(path)
    render = settings.section("render")
    content = settings.section("content")
    failures: list[str] = []
    if (probe.width, probe.height) != (int(render["width"]), int(render["height"])):
        failures.append(f"resolution is {probe.width}x{probe.height}")
    if abs(probe.fps - float(render["fps"])) > 0.05:
        failures.append(f"frame rate is {probe.fps:g} fps")
    if not probe.has_h264:
        failures.append("video codec is not H.264")
    if not probe.has_aac:
        failures.append("audio codec is not AAC")
    if probe.audio_sample_rate != int(render["audio_sample_rate"]):
        failures.append(f"audio sample rate is {probe.audio_sample_rate} Hz")
    if probe.duration_seconds > float(content["hard_max_seconds"]) + 0.25:
        failures.append("runtime exceeds the hard five-minute limit")
    if failures:
        raise ValueError("Media validation failed: " + "; ".join(failures))
    loudness = measure_loudness(path)
    if loudness.true_peak_dbfs > -1.0:
        raise ValueError("Media validation failed: true peak exceeds -1 dBFS")
    warnings: list[str] = []
    if not -18.0 <= loudness.integrated_lufs <= -14.0:
        warnings.append(f"integrated loudness is {loudness.integrated_lufs:g} LUFS")
    if probe.duration_seconds < float(content["target_min_seconds"]) - 0.25:
        warnings.append("runtime is below 90 seconds; upload must remain private with warning")
    if probe.duration_seconds > float(content["target_max_seconds"]) + 0.25:
        warnings.append("runtime is above the preferred three-minute target")
    return MediaValidation(probe=probe, loudness=loudness, warnings=tuple(warnings))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(paths: list[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{sha256_file(path)}  {path.name}" for path in sorted(paths, key=lambda item: item.name)
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
