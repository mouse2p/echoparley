"""Clearly synthetic speech-like signals and planted dialogue structures."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

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
