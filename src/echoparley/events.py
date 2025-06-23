"""Typed events driving full-duplex turn decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EventKind(StrEnum):
    SPEECH_START = "speech_start"
    SPEECH_END = "speech_end"
    DECISION_TICK = "decision_tick"
    GENERATION_READY = "generation_ready"
    UNIT_EMITTED = "unit_emitted"
    TURN_COMPLETE = "turn_complete"
    INTERRUPT = "interrupt"
    RECOVERY_COMPLETE = "recovery_complete"


@dataclass(frozen=True, slots=True)
class EndpointEvent:
    kind: EventKind
    time_ms: int
    posterior: float = 1.0
    speaker: str = "remote"

    def __post_init__(self) -> None:
        if self.time_ms < 0 or not 0 <= self.posterior <= 1 or not self.speaker:
            raise ValueError("endpoint event has invalid time, posterior, or speaker")
