"""Locally synthesized sound anchors. No samples, no provider call, no music bed.

Each shape takes time in seconds from its own onset and returns samples. An episode places
them in measured silence, on something the picture is doing at that moment.
"""

from __future__ import annotations

import numpy as np


# Guitar
def pluck(t, *, hertz=220.0, decay=9.0, gain=0.07):
    """The band itself, at its actual 220 Hz; the drawn motion is explicitly slowed."""
    tone = sum(np.sin(2 * np.pi * hertz * k * t) / k**1.8 for k in range(1, 7))
    return tone * gain * np.exp(-t * decay) * np.minimum(1, t / 0.008)


def thud(t, *, hertz=90.0, decay=13.0, gain=0.05):
    """Cardboard taking up the vibration: low, short, no attack transient to speak of."""
    tone = np.sin(2 * np.pi * hertz * t) + 0.3 * np.sin(2 * np.pi * hertz * 2 * t)
    return tone * gain * np.exp(-t * decay) * np.minimum(1, t / 0.014)


def arrival(t, *, hertz=150.0, gain=0.045):
    """A soft low bloom for the pressure change completing its journey. Not a chime."""
    tone = np.sin(2 * np.pi * hertz * t) + 0.22 * np.sin(2 * np.pi * hertz * 1.5 * t)
    return tone * gain * np.minimum(1, t / 0.13) * np.exp(-t * 3.4)


# Coin
def clack(t, *, hertz=2100.0, decay=52.0, gain=0.05):
    """Metal on glass: a bright, very short transient with no tail to speak of."""
    tone = (
        np.sin(2 * np.pi * hertz * t)
        + 0.6 * np.sin(2 * np.pi * hertz * 1.63 * t)
        + 0.3 * np.sin(2 * np.pi * hertz * 2.41 * t)
    )
    return tone * gain * np.exp(-t * decay) * np.minimum(1, t / 0.001)


def settle(t, *, hertz=1700.0, decay=34.0, gain=0.038):
    """The coin dropping back onto the mouth: lower and softer than the lift."""
    tone = np.sin(2 * np.pi * hertz * t) + 0.45 * np.sin(2 * np.pi * hertz * 1.5 * t)
    return tone * gain * np.exp(-t * decay) * np.minimum(1, t / 0.0015)


def escape(t, *, gain=0.055):
    """Air leaving through the gap. Filtered noise, because that is what escaping air is."""
    generator = np.random.default_rng(4211)
    noise = generator.standard_normal(len(t))
    smoothed = np.convolve(noise, np.ones(48) / 48, mode="same")
    return smoothed * gain * np.minimum(1, t / 0.05) * np.exp(-t * 5.5)


# Falling objects
def knock(t, *, hertz=150.0, decay=26.0, gain=0.07):
    """A stone meeting a wooden floor: a low body and a short bright click on top."""
    body = np.sin(2 * np.pi * hertz * t) + 0.5 * np.sin(2 * np.pi * hertz * 2.7 * t)
    click = np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 140)
    return (body * np.exp(-t * decay) + 0.35 * click) * gain * np.minimum(1, t / 0.0015)


def double_knock(t, *, lag=0.0, gain=0.045):
    """Two things landing; with no lag they are one sound, which is the whole point."""
    first = knock(t, gain=gain)
    shifted = np.clip(t - lag, 0, None)
    second = knock(shifted, hertz=210.0, decay=34.0, gain=gain * 0.6) * (t >= lag)
    return first + second


def crunch(t, *, gain=0.02):
    """Paper being crumpled: short bursts of bright noise, dense at first, then settling."""
    generator = np.random.default_rng(5023)
    noise = np.diff(generator.standard_normal(len(t) + 1))
    bursts = np.zeros_like(t)
    for start in generator.uniform(0, t[-1] * 0.85, 22):
        bursts += np.exp(-np.clip(t - start, 0, None) * 60) * (t >= start)
    return noise * np.clip(bursts, 0, 1) * gain * np.exp(-t * 1.2)
