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
