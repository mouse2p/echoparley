import pytest

from echoparley.latency import TurnLatency


def test_turn_latency_derives_stage_delays() -> None:
    value = TurnLatency(100, 140, 175)
    assert (value.decision_delay_ms, value.first_unit_delay_ms) == (40, 75)


def test_turn_latency_requires_ordered_stages() -> None:
    with pytest.raises(ValueError, match="ordered"):
        TurnLatency(100, 90, 120)


def test_latency_budget_reports_failing_stage() -> None:
    from echoparley.latency import LatencyBudget

    budget = LatencyBudget(50, 100)
    budget.assert_within(TurnLatency(0, 50, 100))
    with pytest.raises(AssertionError, match="decision"):
        budget.assert_within(TurnLatency(0, 51, 80))
    with pytest.raises(AssertionError, match="first-unit"):
        budget.assert_within(TurnLatency(0, 40, 101))


def test_latency_summary_uses_nearest_rank_p95() -> None:
    from echoparley.latency import latency_summary

    values = tuple(TurnLatency(0, delay // 2, delay) for delay in (10, 20, 30, 40))
    assert latency_summary(values) == {
        "count": 4,
        "min_ms": 10,
        "median_ms": 25.0,
        "p95_ms": 40.0,
        "max_ms": 40,
    }
    assert latency_summary(())["count"] == 0
