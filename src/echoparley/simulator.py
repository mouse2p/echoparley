"""Accelerated two-party simulation over planted synthetic dialogues."""

from __future__ import annotations

from dataclasses import dataclass

from echoparley.artifacts import canonical_json
from echoparley.duplex import BargeInMode, DuplexEngine, DuplexState, TurnPolicy
from echoparley.events import EndpointEvent, EventKind
from echoparley.latency import LatencyBudget, TurnLatency
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

    def trace_bytes(self) -> bytes:
        payload = [
            {
                "agent": event.agent,
                "source": event.source,
                "state": event.state.value,
                "time_ms": event.time_ms,
            }
            for event in self.trace
        ]
        return (canonical_json(payload) + "\n").encode()


@dataclass(frozen=True, slots=True)
class StrategySweepPoint:
    mode: BargeInMode
    parameter: float
    yielded: bool
    decision_reason: str


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


def simulate_dialogue(
    scenario: DialogueScenario,
    policy: TurnPolicy | None = None,
    budget: LatencyBudget | None = None,
) -> SimulationResult:
    """Replay planted endpoints into two deterministic turn engines."""
    policy = policy or TurnPolicy()
    budget = budget or LatencyBudget(300, 500)
    engines = {
        speaker: DuplexEngine(policy) for speaker in {turn.speaker for turn in scenario.turns}
    }
    trace: list[TraceEvent] = []
    latencies: list[TurnLatency] = []
    for turn in scenario.turns:
        agent = next(speaker for speaker in sorted(engines) if speaker != turn.speaker)
        engine = engines[agent]
        perception = max(turn.end_ms, engine.last_event_ms)
        engine.handle(EndpointEvent(EventKind.SPEECH_END, perception, speaker=turn.speaker))
        decision = perception + policy.patience_ms
        engine.handle(EndpointEvent(EventKind.DECISION_TICK, decision, speaker=agent))
        first_unit = decision + 20
        transition = engine.handle(
            EndpointEvent(EventKind.GENERATION_READY, first_unit, speaker=agent)
        )
        latency = TurnLatency(perception, decision, first_unit)
        budget.assert_within(latency)
        latencies.append(latency)
        if transition:
            trace.append(TraceEvent(first_unit, agent, engine.state, "response"))
        engine.handle(
            EndpointEvent(EventKind.TURN_COMPLETE, first_unit + policy.min_turn_ms, speaker=agent)
        )
        engine.handle(
            EndpointEvent(
                EventKind.DECISION_TICK, first_unit + policy.min_turn_ms + 1, speaker=agent
            )
        )
    return SimulationResult(
        tuple(trace), tuple(latencies), tuple(turn.end_ms for turn in scenario.turns)
    )


def boundary_agreement(result: SimulationResult, tolerance_ms: int = 250) -> float:
    """Measure response transitions near planted turn endpoints."""
    if tolerance_ms < 0:
        raise ValueError("boundary tolerance must be non-negative")
    if not result.planted_boundaries_ms:
        return 1.0
    matched = sum(
        any(abs(event.time_ms - boundary) <= tolerance_ms for event in result.trace)
        for boundary in result.planted_boundaries_ms
    )
    return round(matched / len(result.planted_boundaries_ms), 6)


def simulation_metadata(scenario: DialogueScenario, result: SimulationResult) -> dict[str, object]:
    """Describe a synthetic run without implying model-quality evaluation."""
    return {
        "data_origin": "synthetic-planted",
        "scenario": scenario.name,
        "seed": scenario.seed,
        "turns": len(scenario.turns),
        "trace_events": len(result.trace),
    }
