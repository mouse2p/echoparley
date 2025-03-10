"""Thin NumPy audio conventions and PCM WAV transport."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class AudioBuffer:
    """Finite mono samples normalized to the closed interval [-1, 1]."""

    samples: FloatArray
    sample_rate: int

    def __post_init__(self) -> None:
        samples = np.asarray(self.samples, dtype=np.float64)
        if samples.ndim != 1:
            raise ValueError("audio samples must be one-dimensional mono")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if not np.all(np.isfinite(samples)):
            raise ValueError("audio samples must be finite")
        if samples.size and np.max(np.abs(samples)) > 1.0:
            raise ValueError("audio samples must be normalized to [-1, 1]")
        samples = samples.copy()
        samples.setflags(write=False)
        object.__setattr__(self, "samples", samples)

    @property
    def duration_seconds(self) -> float:
        return len(self.samples) / self.sample_rate


def encode_pcm16(samples: FloatArray) -> bytes:
    """Encode normalized mono samples as little-endian signed PCM16."""
    values = np.asarray(samples, dtype=np.float64)
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise ValueError("PCM input must be a finite one-dimensional array")
    clipped = np.clip(values, -1.0, 1.0)
    integers = np.where(clipped < 0, clipped * 32768.0, clipped * 32767.0)
    return np.rint(integers).astype("<i2").tobytes()


def decode_pcm16(data: bytes) -> FloatArray:
    """Decode little-endian signed PCM16 into normalized float samples."""
    if len(data) % 2:
        raise ValueError("PCM16 data length must be even")
    integers = np.frombuffer(data, dtype="<i2").astype(np.float64)
    return np.where(integers < 0, integers / 32768.0, integers / 32767.0)
