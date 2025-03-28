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


def mel_filterbank(sample_rate: int, fft_size: int, bands: int) -> FloatArray:
    """Build area-normalized triangular filters across the usable spectrum."""
    if sample_rate <= 0 or fft_size < 2 or bands <= 0:
        raise ValueError("sample_rate, fft_size, and bands must be positive")
    if bands > fft_size // 2:
        raise ValueError("too many mel bands for FFT resolution")
    mel_edges = np.linspace(0.0, float(hertz_to_mel(sample_rate / 2)), bands + 2)
    edges = mel_to_hertz(mel_edges)
    frequencies = np.fft.rfftfreq(fft_size, 1 / sample_rate)
    filters = np.zeros((bands, len(frequencies)), dtype=np.float64)
    for band, (left, center, right) in enumerate(zip(edges, edges[1:], edges[2:], strict=False)):
        filters[band] = np.maximum(
            0.0,
            np.minimum(
                (frequencies - left) / (center - left), (right - frequencies) / (right - center)
            ),
        )
        total = filters[band].sum()
        if total:
            filters[band] /= total
    return filters


def log_mel_features(
    frames: FloatArray, sample_rate: int, bands: int = 40, *, floor: float = 1e-10
) -> FloatArray:
    """Project power spectra onto mel bands and apply a natural-log floor."""
    if floor <= 0 or not np.isfinite(floor):
        raise ValueError("log-mel floor must be finite and positive")
    spectra = power_spectrum(frames)
    filters = mel_filterbank(sample_rate, frames.shape[1], bands)
    return np.log(np.maximum(spectra @ filters.T, floor))


def sliding_statistics(features: FloatArray, radius: int = 2) -> FloatArray:
    """Concatenate local mean and standard deviation with clipped boundaries."""
    values = np.asarray(features, dtype=np.float64)
    if values.ndim != 2 or radius < 0:
        raise ValueError("features must be a matrix and radius non-negative")
    output = np.empty((len(values), values.shape[1] * 2), dtype=np.float64)
    for index in range(len(values)):
        region = values[max(0, index - radius) : index + radius + 1]
        output[index] = np.concatenate((region.mean(axis=0), region.std(axis=0)))
    return output
