import pytest

from echoparley.latency import TurnLatency


def test_turn_latency_derives_stage_delays() -> None:
    value = TurnLatency(100, 140, 175)
    assert (value.decision_delay_ms, value.first_unit_delay_ms) == (40, 75)


def test_turn_latency_requires_ordered_stages() -> None:
    with pytest.raises(ValueError, match="ordered"):
        TurnLatency(100, 90, 120)
