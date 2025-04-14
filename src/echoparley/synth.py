"""Clearly synthetic speech-like signals and planted dialogue structures."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from echoparley.audio import AudioBuffer

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SpeakerProfile:
    """Parameters for a synthetic harmonic signal, not a voice identity."""

    name: str
    fundamental_hz: float
    formants_hz: tuple[float, ...]
    amplitude: float = 0.25

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("speaker name cannot be empty")
        if self.fundamental_hz <= 0 or any(value <= 0 for value in self.formants_hz):
            raise ValueError("synthetic frequencies must be positive")
        if not 0 < self.amplitude <= 1:
            raise ValueError("synthetic amplitude must be in (0, 1]")


def synthesize_formants(
    profile: SpeakerProfile, duration_seconds: float, sample_rate: int, *, seed: int = 0
) -> AudioBuffer:
    """Generate a seeded harmonic-plus-formant fixture with gentle envelopes."""
    if duration_seconds < 0 or sample_rate <= 0:
        raise ValueError("duration must be non-negative and sample_rate positive")
    sample_count = round(duration_seconds * sample_rate)
    if sample_count == 0:
        return AudioBuffer(np.array([], dtype=np.float64), sample_rate)
    time = np.arange(sample_count, dtype=np.float64) / sample_rate
    signal = np.sin(2 * np.pi * profile.fundamental_hz * time)
    for index, frequency in enumerate(profile.formants_hz, 1):
        signal += np.sin(2 * np.pi * frequency * time) / (index + 1)
    rng = np.random.default_rng(seed)
    signal += rng.normal(0.0, 0.01, sample_count)
    ramp = min(sample_count // 2, max(1, round(0.01 * sample_rate)))
    envelope = np.ones(sample_count)
    envelope[:ramp] = np.linspace(0.0, 1.0, ramp, endpoint=False)
    envelope[-ramp:] = np.linspace(1.0, 0.0, ramp, endpoint=False)
    signal *= envelope * profile.amplitude / max(1.0, np.max(np.abs(signal)))
    return AudioBuffer(signal, sample_rate)
