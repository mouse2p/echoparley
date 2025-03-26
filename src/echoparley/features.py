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
