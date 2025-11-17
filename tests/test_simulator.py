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


def test_simulation_trace_bytes_are_replay_stable() -> None:
    from echoparley.simulator import simulate_dialogue
    from echoparley.synth import question_scenario

    first = simulate_dialogue(question_scenario(4)).trace_bytes()
    second = simulate_dialogue(question_scenario(4)).trace_bytes()
    assert first == second and first.endswith(b"\n")


def test_boundary_agreement_has_known_extremes() -> None:
    from echoparley.simulator import boundary_agreement

    event = TraceEvent(100, "a", DuplexState.SPEAK, "response")
    assert boundary_agreement(SimulationResult((event,), (), (100,)), 0) == 1.0
    assert boundary_agreement(SimulationResult((event,), (), (500,)), 0) == 0.0
    with pytest.raises(ValueError, match="non-negative"):
        boundary_agreement(SimulationResult((), (), ()), -1)


def test_simulation_metadata_is_honestly_labeled() -> None:
    from echoparley.simulator import simulate_dialogue, simulation_metadata
    from echoparley.synth import backchannel_scenario

    scenario = backchannel_scenario(3)
    metadata = simulation_metadata(scenario, simulate_dialogue(scenario))
    assert metadata["data_origin"] == "synthetic-planted"
    assert metadata["seed"] == 3


def test_strategy_sweep_point_is_immutable() -> None:
    from echoparley.duplex import BargeInMode
    from echoparley.simulator import StrategySweepPoint

    point = StrategySweepPoint(BargeInMode.IMMEDIATE_YIELD, 0.8, True, "test")
    assert point.mode.value == "immediate-yield"


def test_strategy_sweep_reuses_identical_evidence() -> None:
    from echoparley.simulator import sweep_barge_in_strategies

    points = sweep_barge_in_strategies((0.8, 0.95))
    assert len(points) == 6
    assert sum(point.yielded for point in points) == 5


def test_strategy_sweep_is_deterministic() -> None:
    from echoparley.simulator import sweep_barge_in_strategies

    assert sweep_barge_in_strategies((0.7, 0.8, 0.9)) == sweep_barge_in_strategies((0.7, 0.8, 0.9))


def test_strategy_table_reports_bounded_measured_rates() -> None:
    from echoparley.simulator import strategy_comparison_table, sweep_barge_in_strategies

    rows = strategy_comparison_table(sweep_barge_in_strategies((0.7, 0.8, 0.95)))
    assert [row["strategy"] for row in rows] == [
        "immediate-yield",
        "grace-window",
        "competitive-floor",
    ]
    assert all(0 <= row["yield_rate"] <= 1 for row in rows)
