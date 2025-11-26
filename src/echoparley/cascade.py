"""Explicit STT-to-text-LM-to-TTS comparison path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from echoparley.adapters import AdapterAction
from echoparley.events import EndpointEvent
from echoparley.stream import UnifiedStream


class TextStage(Protocol):
    def __call__(self, value: str) -> str: ...


@dataclass(frozen=True, slots=True)
class VoiceActivitySpan:
    start_frame: int
    end_frame: int


@dataclass(frozen=True, slots=True)
class MockVAD:
    """Energy threshold stage for offline synthetic fixtures."""

    threshold: float = 0.05

    def __post_init__(self) -> None:
        if self.threshold < 0:
            raise ValueError("VAD threshold must be non-negative")

    def __call__(self, frame_energy: NDArray[np.float64]) -> tuple[VoiceActivitySpan, ...]:
        values = np.asarray(frame_energy, dtype=np.float64)
        if values.ndim != 1 or not np.all(np.isfinite(values)):
            raise ValueError("VAD energy must be a finite vector")
        active = values >= self.threshold
        boundaries = np.flatnonzero(np.diff(np.concatenate(([False], active, [False]))))
        return tuple(
            VoiceActivitySpan(int(start), int(end)) for start, end in boundaries.reshape(-1, 2)
        )


@dataclass(frozen=True, slots=True)
class CascadeResult:
    transcript: str
    response: str
    units: tuple[int, ...]
    stage_delays_ms: tuple[int, int, int]

    @property
    def total_delay_ms(self) -> int:
        return sum(self.stage_delays_ms)


@dataclass(frozen=True, slots=True)
class ScriptedCascade:
    stt: TextStage
    text_lm: TextStage
    tts: TextStage
    stage_delays_ms: tuple[int, int, int] = (80, 60, 90)

    def run(self, audio_label: str) -> CascadeResult:
        transcript = self.stt(audio_label)
        response = self.text_lm(transcript)
        encoded = self.tts(response)
        return CascadeResult(
            transcript,
            response,
            tuple(ord(character) % 32 for character in encoded),
            self.stage_delays_ms,
        )

    def __post_init__(self) -> None:
        if any(delay < 0 for delay in self.stage_delays_ms):
            raise ValueError("cascade stage delays must be non-negative")


def compare_paths(
    cascade: CascadeResult, direct_delay_ms: int, direct_units: tuple[int, ...]
) -> dict[str, int | str]:
    """Compare measured synthetic path latency and unit counts."""
    if direct_delay_ms < 0:
        raise ValueError("direct delay must be non-negative")
    winner = (
        "direct"
        if direct_delay_ms < cascade.total_delay_ms
        else "cascade"
        if cascade.total_delay_ms < direct_delay_ms
        else "tie"
    )
    return {
        "cascade_ms": cascade.total_delay_ms,
        "direct_ms": direct_delay_ms,
        "latency_winner": winner,
        "cascade_units": len(cascade.units),
        "direct_units": len(direct_units),
    }


@dataclass(slots=True)
class CascadeAdapter:
    cascade: ScriptedCascade
    latest_label: str = "silence"

    def observe(self, value: UnifiedStream) -> None:
        self.latest_label = " ".join(token.value for token in value.tokens)

    def act(self, events: tuple[EndpointEvent, ...]) -> AdapterAction:
        del events
        result = self.cascade.run(self.latest_label)
        return AdapterAction(
            tuple(f"<unit:{unit}>" for unit in result.units), result.total_delay_ms
        )


@dataclass(frozen=True, slots=True)
class MockPunctuation:
    """Deterministic transcript casing and terminal punctuation stage."""

    terminal: str = "."

    def __post_init__(self) -> None:
        if self.terminal not in {".", "?", "!"}:
            raise ValueError("unsupported terminal punctuation")

    def __call__(self, value: str) -> str:
        text = " ".join(value.split())
        if not text:
            return ""
        restored = text[0].upper() + text[1:]
        return restored if restored[-1] in ".?!" else restored + self.terminal


@dataclass(frozen=True, slots=True)
class AlignedTTSUnit:
    identifier: int
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True, slots=True)
class MockTTSAlignment:
    unit_ms: int = 40

    def __post_init__(self) -> None:
        if self.unit_ms <= 0:
            raise ValueError("TTS unit duration must be positive")

    def __call__(self, text: str) -> tuple[AlignedTTSUnit, ...]:
        words = text.split()
        return tuple(
            AlignedTTSUnit(
                sum(map(ord, word)) % 64, index * self.unit_ms, (index + 1) * self.unit_ms, word
            )
            for index, word in enumerate(words)
        )


@dataclass(frozen=True, slots=True)
class StageTiming:
    name: str
    delay_ms: int

    def __post_init__(self) -> None:
        if not self.name or self.delay_ms < 0:
            raise ValueError("stage timing requires a name and non-negative delay")


@dataclass(frozen=True, slots=True)
class StageLatencyLedger:
    timings: tuple[StageTiming, ...] = ()

    @property
    def total_ms(self) -> int:
        return sum(item.delay_ms for item in self.timings)

    def append(self, name: str, delay_ms: int) -> StageLatencyLedger:
        return StageLatencyLedger((*self.timings, StageTiming(name, delay_ms)))
