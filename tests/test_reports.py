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


def test_empty_session_timeline_still_has_a_label() -> None:
    from echoparley.reports import session_timeline_group

    assert session_timeline_group((), label="empty") == '<text x="20" y="22">empty</text>'


def test_session_timeline_rejects_time_regression() -> None:
    import pytest

    from echoparley.reports import session_timeline_group
    from echoparley.session import SessionEvent

    with pytest.raises(ValueError, match="chronological"):
        session_timeline_group(
            (SessionEvent(0, 2, "a", {}), SessionEvent(1, 1, "b", {})), label="bad"
        )


def test_side_by_side_timeline_places_sessions_in_separate_columns() -> None:
    from echoparley.reports import side_by_side_session_svg
    from echoparley.session import SessionEvent

    event = SessionEvent(0, 0, "tick", {})
    svg = side_by_side_session_svg((event,), (event,), left_label="A", right_label="B")
    assert '<text x="20" y="22">A</text>' in svg
    assert '<text x="420" y="22">B</text>' in svg


def test_event_diff_rows_use_insert_delete_change_classes() -> None:
    from echoparley.reports import event_diff_rows
    from echoparley.session import SessionEvent, diff_sessions

    left = (SessionEvent(0, 0, "old", {}), SessionEvent(1, 1, "tail", {}))
    right = (SessionEvent(0, 0, "new", {}),)
    rows = event_diff_rows(diff_sessions(left, right))
    assert 'class="diff change"' in rows[0]
    assert 'class="diff delete"' in rows[1]


def test_event_diff_rows_render_inserted_tails() -> None:
    from echoparley.reports import event_diff_rows
    from echoparley.session import SessionEvent, diff_sessions

    rows = event_diff_rows(diff_sessions((), (SessionEvent(0, 0, "added", {}),)))
    assert 'class="diff insert"' in rows[0]
    assert "∅ → added" in rows[0]


def test_event_diff_svg_is_deterministic_and_escaped() -> None:
    from echoparley.reports import event_diff_svg
    from echoparley.session import SessionEvent, diff_sessions

    diff = diff_sessions((SessionEvent(0, 0, "a", {}),), (SessionEvent(0, 0, "b", {}),))
    svg = event_diff_svg(diff, title="A < B")
    assert svg == event_diff_svg(diff, title="A < B")
    assert "A &lt; B" in svg


def test_session_diff_report_combines_timelines_and_rows() -> None:
    from echoparley.reports import session_diff_report_svg
    from echoparley.session import SessionEvent

    svg = session_diff_report_svg((SessionEvent(0, 0, "a", {}),), (SessionEvent(0, 1, "b", {}),))
    assert "left" in svg and "right" in svg
    assert 'class="diff change"' in svg
