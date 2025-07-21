"""Accelerated two-party simulation over planted synthetic dialogues."""

from __future__ import annotations

from dataclasses import dataclass

from echoparley.duplex import DuplexState
from echoparley.events import EndpointEvent, EventKind
from echoparley.latency import TurnLatency
from echoparley.synth import DialogueScenario


@dataclass(frozen=True, slots=True)
class TraceEvent:
    time_ms: int
    agent: str
    state: DuplexState
    source: str


@dataclass(frozen=True, slots=True)
class SimulationResult:
    trace: tuple[TraceEvent, ...]
    latencies: tuple[TurnLatency, ...]
    planted_boundaries_ms: tuple[int, ...]


def planted_events(scenario: DialogueScenario) -> tuple[EndpointEvent, ...]:
    """Convert annotations into stable start/end events, preserving overlaps."""
    events = [
        event
        for turn in scenario.turns
        for event in (
            EndpointEvent(EventKind.SPEECH_START, turn.start_ms, speaker=turn.speaker),
            EndpointEvent(
                EventKind.INTERRUPT if turn.kind == "interrupt" else EventKind.SPEECH_END,
                turn.end_ms,
                speaker=turn.speaker,
            ),
        )
    ]
    return tuple(sorted(events, key=lambda item: (item.time_ms, item.kind.value, item.speaker)))
