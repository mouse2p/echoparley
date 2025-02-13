"""Validated configuration shared by offline experiments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    """Core reproducibility and audio conventions for a run."""

    seed: int = 0
    sample_rate: int = 16_000
    frame_ms: float = 20.0
    hop_ms: float = 10.0

    def __post_init__(self) -> None:
        numeric_values = (self.seed, self.sample_rate, self.frame_ms, self.hop_ms)
        if any(isinstance(value, bool) for value in numeric_values):
            raise TypeError("boolean values are not valid numeric configuration")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        if not 8_000 <= self.sample_rate <= 48_000:
            raise ValueError("sample_rate must be between 8000 and 48000")
        if self.frame_ms <= 0 or self.hop_ms <= 0:
            raise ValueError("frame_ms and hop_ms must be positive")
        if self.hop_ms > self.frame_ms:
            raise ValueError("hop_ms cannot exceed frame_ms")

    @property
    def frame_samples(self) -> int:
        """Return the rounded frame size in samples."""
        return round(self.sample_rate * self.frame_ms / 1000)

    @property
    def hop_samples(self) -> int:
        """Return the rounded hop size in samples."""
        return round(self.sample_rate * self.hop_ms / 1000)
