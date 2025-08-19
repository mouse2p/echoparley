"""Deterministic prosodic measurements for synthetic speech fixtures."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class PitchTrack:
    """Frame-center times, F0 estimates, and normalized voicing strengths."""

    times_seconds: FloatArray
    frequencies_hz: FloatArray
    strengths: FloatArray


def _validate_pitch_parameters(
    sample_rate: int,
    frame_size: int,
    hop_size: int,
    min_hz: float,
    max_hz: float,
    voicing_threshold: float,
) -> None:
    if sample_rate <= 0 or frame_size <= 1 or hop_size <= 0:
        raise ValueError("pitch framing parameters are invalid")
    if not 0 < min_hz < max_hz < sample_rate / 2 or not 0 <= voicing_threshold <= 1:
        raise ValueError("pitch range or voicing threshold is invalid")


def autocorrelation_f0(
    samples: FloatArray,
    sample_rate: int,
    *,
    frame_size: int = 320,
    hop_size: int = 160,
    min_hz: float = 60.0,
    max_hz: float = 400.0,
    voicing_threshold: float = 0.25,
) -> PitchTrack:
    """Estimate frame-level F0 without external models or downloaded weights."""
    signal = np.asarray(samples, dtype=np.float64)
    if signal.ndim != 1:
        raise ValueError("pitch input must be one-dimensional")
    _validate_pitch_parameters(sample_rate, frame_size, hop_size, min_hz, max_hz, voicing_threshold)
    if len(signal) < frame_size:
        empty = np.array([], dtype=np.float64)
        return PitchTrack(empty, empty.copy(), empty.copy())
    lag_min = max(1, int(np.floor(sample_rate / max_hz)))
    lag_max = min(frame_size - 1, int(np.ceil(sample_rate / min_hz)))
    window = np.hanning(frame_size)
    starts = range(0, len(signal) - frame_size + 1, hop_size)
    frequencies: list[float] = []
    strengths: list[float] = []
    times: list[float] = []
    for start in starts:
        frame = (
            signal[start : start + frame_size] - np.mean(signal[start : start + frame_size])
        ) * window
        energy = float(np.dot(frame, frame))
        times.append((start + frame_size / 2) / sample_rate)
        if energy <= np.finfo(np.float64).eps:
            frequencies.append(0.0)
            strengths.append(0.0)
            continue
        correlation = np.correlate(frame, frame, mode="full")[frame_size - 1 :]
        region = correlation[lag_min : lag_max + 1] / energy
        offset = int(np.argmax(region))
        lag = lag_min + offset
        strength = float(np.clip(region[offset], 0.0, 1.0))
        frequencies.append(round(sample_rate / lag, 6) if strength >= voicing_threshold else 0.0)
        strengths.append(round(strength, 6))
    return PitchTrack(np.asarray(times), np.asarray(frequencies), np.asarray(strengths))
