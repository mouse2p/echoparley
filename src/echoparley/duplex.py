"""Explicit full-duplex turn-taking state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class TurnPolicy:
    patience_ms: int = 200
    hangover_ms: int = 120
    min_turn_ms: int = 100
    max_turn_ms: int = 10_000
    interrupt_threshold: float = 0.75

    def __post_init__(self) -> None:
        if min(self.patience_ms, self.hangover_ms, self.min_turn_ms) < 0:
            raise ValueError("turn policy durations must be non-negative")
        if self.max_turn_ms <= self.min_turn_ms:
            raise ValueError("max_turn_ms must exceed min_turn_ms")
        if not 0 <= self.interrupt_threshold <= 1:
            raise ValueError("interrupt_threshold must be a probability")


class DuplexState(StrEnum):
    LISTEN = "LISTEN"
    TAKE_FLOOR = "TAKE_FLOOR"
    SPEAK = "SPEAK"
    YIELD = "YIELD"
    BARGE_IN = "BARGE_IN"
    RECOVER = "RECOVER"
