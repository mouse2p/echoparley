from dataclasses import FrozenInstanceError

import pytest

from echoparley.duplex import DuplexState
from echoparley.simulator import SimulationResult, TraceEvent


def test_simulation_trace_events_are_immutable() -> None:
    event = TraceEvent(0, "a", DuplexState.LISTEN, "start")
    result = SimulationResult((event,), (), ())
    with pytest.raises(FrozenInstanceError):
        result.trace[0].time_ms = 1  # type: ignore[misc]
