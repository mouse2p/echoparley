import pytest

from echoparley.duplex import DuplexState
from echoparley.reports import latency_histogram, svg_report
from echoparley.simulator import SimulationResult, TraceEvent


def test_svg_report_is_deterministic_and_escaped() -> None:
    result = SimulationResult((TraceEvent(10, "a", DuplexState.SPEAK, "response"),), (), (0,))
    first = svg_report(result, {"f1": 1.0}, title="A < B")
    assert first == svg_report(result, {"f1": 1.0}, title="A < B")
    assert "A &lt; B" in first and 'data-origin="synthetic-planted"' in first
    assert first.endswith("</svg>\n")


def test_latency_histogram_uses_half_open_bins() -> None:
    assert latency_histogram((0, 49, 50, 101), 50) == ((0, 2), (50, 1), (100, 1))
    with pytest.raises(ValueError):
        latency_histogram((-1,))


def test_strategy_comparison_svg_is_stable_and_labeled() -> None:
    from echoparley.reports import strategy_comparison_svg

    svg = strategy_comparison_svg(({"strategy": "grace-window", "yield_rate": 0.5},))
    assert 'width="200"' in svg
    assert "synthetic-planted" in svg and svg.endswith("\n")


def test_session_timeline_group_scales_events_and_escapes_labels() -> None:
    from echoparley.reports import session_timeline_group
    from echoparley.session import SessionEvent

    group = session_timeline_group((SessionEvent(0, 10, "a<b", {}),), label="left & first")
    assert "left &amp; first" in group and "a&lt;b" in group
    assert 'cx="340"' in group
