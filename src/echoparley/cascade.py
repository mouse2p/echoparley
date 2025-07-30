"""Explicit STT-to-text-LM-to-TTS comparison path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class TextStage(Protocol):
    def __call__(self, value: str) -> str: ...


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
