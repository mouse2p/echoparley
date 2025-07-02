"""Explicit full-duplex turn-taking state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from echoparley.events import EndpointEvent, EventKind


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


@dataclass(frozen=True, slots=True)
class Transition:
    previous: DuplexState
    current: DuplexState
    event: EventKind
    time_ms: int
    reason: str


@dataclass(slots=True)
class DuplexEngine:
    """Deterministic state machine with explicit partial-generation state."""

    policy: TurnPolicy = field(default_factory=TurnPolicy)
    state: DuplexState = DuplexState.LISTEN
    transitions: list[Transition] = field(default_factory=list)
    partial_units: list[int] = field(default_factory=list)
    remote_end_ms: int | None = None
    speaking_since_ms: int | None = None

    def _move(self, current: DuplexState, event: EndpointEvent, reason: str) -> Transition:
        transition = Transition(self.state, current, event.kind, event.time_ms, reason)
        self.state = current
        self.transitions.append(transition)
        return transition

    def handle(self, event: EndpointEvent) -> Transition | None:
        """Consume one event and perform at most one state transition."""
        if self.transitions and event.time_ms < self.transitions[-1].time_ms:
            raise ValueError("duplex events must be chronological")
        if self.state is DuplexState.LISTEN:
            if event.kind is EventKind.SPEECH_START:
                self.remote_end_ms = None
            elif event.kind is EventKind.SPEECH_END:
                self.remote_end_ms = event.time_ms
            elif (
                event.kind is EventKind.DECISION_TICK
                and self.remote_end_ms is not None
                and event.time_ms - self.remote_end_ms >= self.policy.patience_ms
            ):
                return self._move(DuplexState.TAKE_FLOOR, event, "endpoint patience elapsed")
        return None
