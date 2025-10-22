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


class BargeInMode(StrEnum):
    IMMEDIATE_YIELD = "immediate-yield"
    GRACE_WINDOW = "grace-window"
    COMPETITIVE_FLOOR = "competitive-floor"


@dataclass(frozen=True, slots=True)
class BargeInStrategy:
    mode: BargeInMode = BargeInMode.IMMEDIATE_YIELD
    grace_ms: int = 120
    competitive_threshold: float = 0.9

    def __post_init__(self) -> None:
        if self.grace_ms < 0 or not 0 <= self.competitive_threshold <= 1:
            raise ValueError("barge-in strategy parameters are invalid")


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
    barge_in_strategy: BargeInStrategy = field(default_factory=BargeInStrategy)
    state: DuplexState = DuplexState.LISTEN
    transitions: list[Transition] = field(default_factory=list)
    partial_units: list[int] = field(default_factory=list)
    remote_end_ms: int | None = None
    speaking_since_ms: int | None = None
    last_event_ms: int = -1

    def _move(self, current: DuplexState, event: EndpointEvent, reason: str) -> Transition:
        transition = Transition(self.state, current, event.kind, event.time_ms, reason)
        self.state = current
        self.transitions.append(transition)
        return transition

    def handle(self, event: EndpointEvent) -> Transition | None:
        """Consume one event and perform at most one state transition."""
        if event.time_ms < self.last_event_ms:
            raise ValueError("duplex events must be chronological")
        self.last_event_ms = event.time_ms
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
        elif self.state is DuplexState.TAKE_FLOOR and event.kind is EventKind.GENERATION_READY:
            self.speaking_since_ms = event.time_ms
            return self._move(DuplexState.SPEAK, event, "first unit ready")
        elif self.state is DuplexState.SPEAK and event.kind is EventKind.UNIT_EMITTED:
            self.partial_units.append(round(event.posterior * 1000))
        elif self.state is DuplexState.SPEAK and event.kind in {
            EventKind.INTERRUPT,
            EventKind.SPEECH_START,
        }:
            elapsed = event.time_ms - (self.speaking_since_ms or event.time_ms)
            decision = decide_interruption(
                self.barge_in_strategy,
                posterior=event.posterior,
                threshold=self.policy.interrupt_threshold,
                elapsed_speaking_ms=elapsed,
            )
            if decision.should_yield:
                return self._move(DuplexState.BARGE_IN, event, decision.reason)
        elif self.state is DuplexState.SPEAK and (
            event.kind is EventKind.TURN_COMPLETE
            or (
                event.kind is EventKind.DECISION_TICK
                and self.speaking_since_ms is not None
                and event.time_ms - self.speaking_since_ms >= self.policy.max_turn_ms
            )
        ):
            return self._move(DuplexState.YIELD, event, "turn complete or maximum reached")
        elif self.state is DuplexState.YIELD and event.kind is EventKind.DECISION_TICK:
            self.partial_units.clear()
            self.speaking_since_ms = None
            return self._move(DuplexState.LISTEN, event, "yield completed")
        elif self.state is DuplexState.BARGE_IN and event.kind is EventKind.DECISION_TICK:
            self.partial_units.clear()
            self.speaking_since_ms = None
            return self._move(DuplexState.RECOVER, event, "partial generation flushed")
        elif self.state is DuplexState.RECOVER and event.kind is EventKind.RECOVERY_COMPLETE:
            self.remote_end_ms = None
            return self._move(DuplexState.LISTEN, event, "recovery completed")
        return None


@dataclass(frozen=True, slots=True)
class InterruptionDecision:
    should_yield: bool
    reason: str


def decide_interruption(
    strategy: BargeInStrategy,
    *,
    posterior: float,
    threshold: float,
    elapsed_speaking_ms: int,
) -> InterruptionDecision:
    """Apply one deterministic barge-in strategy to a remote speech claim."""
    if not 0 <= posterior <= 1 or not 0 <= threshold <= 1 or elapsed_speaking_ms < 0:
        raise ValueError("interruption evidence is invalid")
    if posterior < threshold:
        return InterruptionDecision(False, "below interrupt threshold")
    if strategy.mode is BargeInMode.IMMEDIATE_YIELD:
        return InterruptionDecision(True, "immediate confident interruption")
    if strategy.mode is BargeInMode.GRACE_WINDOW:
        if elapsed_speaking_ms >= strategy.grace_ms:
            return InterruptionDecision(True, "grace window elapsed")
        return InterruptionDecision(False, "inside grace window")
    if posterior >= max(threshold, strategy.competitive_threshold):
        return InterruptionDecision(True, "remote won competitive floor")
    return InterruptionDecision(False, "strategy retained floor")
