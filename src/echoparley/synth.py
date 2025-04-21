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


TURN_KINDS = frozenset({"turn", "backchannel", "interrupt", "hold"})


@dataclass(frozen=True, slots=True)
class TurnAnnotation:
    """Ground-truth interval deliberately planted by a scenario template."""

    speaker: str
    start_ms: int
    end_ms: int
    text: str
    kind: str = "turn"
    topic: str | None = None

    def __post_init__(self) -> None:
        if not self.speaker or self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("turn requires a speaker and a positive interval")
        if self.kind not in TURN_KINDS:
            raise ValueError(f"unknown turn kind: {self.kind}")


@dataclass(frozen=True, slots=True)
class DialogueScenario:
    """A reproducible two-party script with explicit planted ground truth."""

    name: str
    seed: int
    turns: tuple[TurnAnnotation, ...]

    def __post_init__(self) -> None:
        if not self.name or self.seed < 0 or not self.turns:
            raise ValueError("scenario requires a name, non-negative seed, and turns")
        if len({turn.speaker for turn in self.turns}) > 2:
            raise ValueError("synthetic dialogue supports at most two speakers")
        if tuple(sorted(self.turns, key=lambda turn: (turn.start_ms, turn.end_ms))) != self.turns:
            raise ValueError("scenario turns must be sorted by start time")

    @property
    def duration_ms(self) -> int:
        return max(turn.end_ms for turn in self.turns)

    def overlaps(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            (left, right)
            for left, first in enumerate(self.turns)
            for right, second in enumerate(self.turns[left + 1 :], left + 1)
            if first.speaker != second.speaker and second.start_ms < first.end_ms
        )
