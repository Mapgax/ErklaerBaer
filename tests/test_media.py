import wave

import numpy as np

from erklaerbaer.media import measure_loudness, mux_and_normalize, probe_media, validate_media
from erklaerbaer.renderer import PaperCutRenderer

from .factories import make_settings, sample_storyboard


def test_short_render_has_required_codecs(tmp_path):
    settings = make_settings(tmp_path)
    storyboard = sample_storyboard()
    renderer = PaperCutRenderer(settings, width=320, height=180, fps=5)
    silent = tmp_path / "silent.mp4"
    audio = tmp_path / "audio.wav"
    final = tmp_path / "final.mp4"
    durations = [0.2] * len(storyboard.scenes)
    renderer.render_video(storyboard, durations, silent)
    times = np.arange(round(sum(durations) * 48_000)) / 48_000
    samples = (np.sin(times * 2 * np.pi * 440) * 500).astype("<i2")
    with wave.open(str(audio), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(48_000)
        handle.writeframes(samples.tobytes())
    mux_and_normalize(silent, audio, final)
    probe = probe_media(final)
    assert (probe.width, probe.height) == (320, 180)
    assert abs(probe.fps - 5) < 0.05
    assert probe.has_h264
    assert probe.has_aac
    assert probe.audio_sample_rate == 48_000
    settings.raw["render"].update({"width": 320, "height": 180, "fps": 5})
    validation = validate_media(final, settings)
    assert validation.warnings
    assert -18 <= validation.loudness.integrated_lufs <= -14
    assert validation.loudness.true_peak_dbfs <= -1
    loudness = measure_loudness(final)
    assert -18 <= loudness.integrated_lufs <= -14
    assert loudness.true_peak_dbfs <= -1
