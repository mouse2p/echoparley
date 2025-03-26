"""Deterministic NumPy speech features with explicit numeric floors."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def analysis_window(length: int, kind: str = "hann") -> FloatArray:
    """Return a periodic Hann, Hamming, or rectangular window."""
    if length <= 0:
        raise ValueError("window length must be positive")
    if kind == "rectangular":
        return np.ones(length, dtype=np.float64)
    indices = np.arange(length, dtype=np.float64)
    phase = 2 * np.pi * indices / length
    if kind == "hann":
        return 0.5 - 0.5 * np.cos(phase)
    if kind == "hamming":
        return 0.54 - 0.46 * np.cos(phase)
    raise ValueError(f"unknown window kind: {kind}")


def power_spectrum(frames: FloatArray, *, window: str = "hann") -> FloatArray:
    """Compute squared-magnitude real FFT spectra for a frame matrix."""
    values = np.asarray(frames, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] == 0:
        raise ValueError("frames must be a nonempty-width matrix")
    transformed = np.fft.rfft(values * analysis_window(values.shape[1], window), axis=1)
    return np.abs(transformed) ** 2 / values.shape[1]


def hertz_to_mel(frequency: FloatArray | float) -> FloatArray:
    """Map non-negative Hertz values to the HTK mel convention."""
    values = np.asarray(frequency, dtype=np.float64)
    if np.any(values < 0) or not np.all(np.isfinite(values)):
        raise ValueError("frequencies must be finite and non-negative")
    return 2595.0 * np.log10(1.0 + values / 700.0)


def mel_to_hertz(mels: FloatArray | float) -> FloatArray:
    """Invert the HTK mel transform for non-negative values."""
    values = np.asarray(mels, dtype=np.float64)
    if np.any(values < 0) or not np.all(np.isfinite(values)):
        raise ValueError("mel values must be finite and non-negative")
    return 700.0 * (10.0 ** (values / 2595.0) - 1.0)
