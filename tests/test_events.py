import pytest

from echoparley.events import EndpointEvent, EventKind


def test_endpoint_event_accepts_probability_boundaries() -> None:
    assert EndpointEvent(EventKind.SPEECH_START, 0, 0.0).posterior == 0.0
    assert EndpointEvent(EventKind.SPEECH_END, 1, 1.0).posterior == 1.0


@pytest.mark.parametrize("time,posterior", [(-1, 0.5), (0, -0.1), (0, 1.1)])
def test_endpoint_event_rejects_invalid_values(time: int, posterior: float) -> None:
    with pytest.raises(ValueError, match="invalid"):
        EndpointEvent(EventKind.DECISION_TICK, time, posterior)
