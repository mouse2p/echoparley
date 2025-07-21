from dataclasses import FrozenInstanceError

import pytest

from echoparley.duplex import DuplexState
from echoparley.simulator import SimulationResult, TraceEvent


def test_simulation_trace_events_are_immutable() -> None:
    event = TraceEvent(0, "a", DuplexState.LISTEN, "start")
    result = SimulationResult((event,), (), ())
    with pytest.raises(FrozenInstanceError):
        result.trace[0].time_ms = 1  # type: ignore[misc]


def test_planted_events_are_time_sorted() -> None:
    from echoparley.simulator import planted_events
    from echoparley.synth import barge_in_scenario

    events = planted_events(barge_in_scenario(0))
    assert [event.time_ms for event in events] == sorted(event.time_ms for event in events)
    assert any(event.kind.value == "interrupt" for event in events)


def test_simulation_is_deterministic_and_budgeted() -> None:
    from echoparley.latency import LatencyBudget
    from echoparley.simulator import simulate_dialogue
    from echoparley.synth import booking_scenario

    scenario = booking_scenario(2)
    result = simulate_dialogue(scenario)
    assert result == simulate_dialogue(scenario)
    assert len(result.latencies) == len(scenario.turns)
    with pytest.raises(AssertionError, match="decision"):
        simulate_dialogue(scenario, budget=LatencyBudget(100, 500))
