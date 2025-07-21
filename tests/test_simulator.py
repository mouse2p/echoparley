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
