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
    if signal.ndim != 1 or not np.all(np.isfinite(signal)):
        raise ValueError("pitch input must be a finite one-dimensional signal")
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


def moving_average_contour(values: FloatArray, width: int = 3) -> FloatArray:
    """Smooth voiced F0 values while leaving unvoiced frames at zero."""
    contour = np.asarray(values, dtype=np.float64)
    if contour.ndim != 1 or width <= 0 or width % 2 == 0:
        raise ValueError("moving-average width must be a positive odd integer")
    if len(contour) == 0:
        return contour.copy()
    radius = width // 2
    output = np.zeros_like(contour)
    for index, value in enumerate(contour):
        if value == 0:
            continue
        neighborhood = contour[max(0, index - radius) : min(len(contour), index + radius + 1)]
        voiced = neighborhood[neighborhood > 0]
        output[index] = np.mean(voiced) if len(voiced) else 0.0
    return np.round(output, 6)


@dataclass(frozen=True, slots=True)
class ToneEvent:
    """A local synthetic pitch movement at a frame time."""

    kind: str
    time_seconds: float
    change_hz: float


def annotate_tone_events(
    track: PitchTrack, *, rise_threshold_hz: float = 20.0
) -> tuple[ToneEvent, ...]:
    """Label adjacent voiced rises and falls in a synthetic pitch track."""
    if rise_threshold_hz <= 0:
        raise ValueError("tone threshold must be positive")
    if not (len(track.times_seconds) == len(track.frequencies_hz) == len(track.strengths)):
        raise ValueError("pitch track arrays must have equal lengths")
    events: list[ToneEvent] = []
    for index in range(1, len(track.frequencies_hz)):
        before, after = track.frequencies_hz[index - 1 : index + 1]
        if before <= 0 or after <= 0:
            continue
        change = float(after - before)
        if abs(change) >= rise_threshold_hz:
            events.append(
                ToneEvent(
                    "rise" if change > 0 else "fall",
                    round(float(track.times_seconds[index]), 6),
                    round(change, 6),
                )
            )
    return tuple(events)
