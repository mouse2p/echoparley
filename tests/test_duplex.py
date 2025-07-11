import pytest

from echoparley.duplex import TurnPolicy


def test_default_turn_policy_is_valid() -> None:
    assert TurnPolicy().min_turn_ms < TurnPolicy().max_turn_ms


@pytest.mark.parametrize(
    "changes",
    [{"patience_ms": -1}, {"min_turn_ms": 10, "max_turn_ms": 10}, {"interrupt_threshold": 1.1}],
)
def test_turn_policy_rejects_invalid_parameters(changes: dict[str, int | float]) -> None:
    with pytest.raises(ValueError):
        TurnPolicy(**changes)


def test_duplex_engine_starts_cleanly_in_listen() -> None:
    from echoparley.duplex import DuplexEngine, DuplexState

    engine = DuplexEngine()
    assert engine.state is DuplexState.LISTEN
    assert engine.transitions == [] and engine.partial_units == []


def test_endpoint_patience_controls_floor_take() -> None:
    from echoparley.duplex import DuplexEngine, DuplexState
    from echoparley.events import EndpointEvent, EventKind

    engine = DuplexEngine(TurnPolicy(patience_ms=50))
    engine.handle(EndpointEvent(EventKind.SPEECH_END, 100))
    assert engine.handle(EndpointEvent(EventKind.DECISION_TICK, 149)) is None
    transition = engine.handle(EndpointEvent(EventKind.DECISION_TICK, 150))
    assert transition is not None and engine.state is DuplexState.TAKE_FLOOR


def test_generation_ready_cannot_skip_take_floor() -> None:
    from echoparley.duplex import DuplexEngine, DuplexState
    from echoparley.events import EndpointEvent, EventKind

    engine = DuplexEngine()
    assert engine.handle(EndpointEvent(EventKind.GENERATION_READY, 0)) is None
    assert engine.state is DuplexState.LISTEN
    engine.handle(EndpointEvent(EventKind.SPEECH_END, 1))
    engine.handle(EndpointEvent(EventKind.DECISION_TICK, 201))
    transition = engine.handle(EndpointEvent(EventKind.GENERATION_READY, 220))
    assert transition is not None and transition.previous is DuplexState.TAKE_FLOOR


def test_speaking_engine_collects_partial_units() -> None:
    from echoparley.duplex import DuplexEngine
    from echoparley.events import EndpointEvent, EventKind

    engine = DuplexEngine()
    for event in (
        EndpointEvent(EventKind.SPEECH_END, 0),
        EndpointEvent(EventKind.DECISION_TICK, 200),
        EndpointEvent(EventKind.GENERATION_READY, 210),
        EndpointEvent(EventKind.UNIT_EMITTED, 220, 0.123),
    ):
        engine.handle(event)
    assert engine.partial_units == [123]


def test_turn_completion_yields_then_listens() -> None:
    from echoparley.duplex import DuplexEngine, DuplexState
    from echoparley.events import EndpointEvent, EventKind

    engine = DuplexEngine()
    for kind, time in (
        (EventKind.SPEECH_END, 0),
        (EventKind.DECISION_TICK, 200),
        (EventKind.GENERATION_READY, 210),
        (EventKind.TURN_COMPLETE, 300),
        (EventKind.DECISION_TICK, 301),
    ):
        engine.handle(EndpointEvent(kind, time))
    assert engine.state is DuplexState.LISTEN
    assert [item.current for item in engine.transitions][-2:] == [
        DuplexState.YIELD,
        DuplexState.LISTEN,
    ]


def test_interrupt_threshold_controls_barge_in() -> None:
    from echoparley.duplex import DuplexEngine, DuplexState
    from echoparley.events import EndpointEvent, EventKind

    engine = DuplexEngine()
    for event in (
        EndpointEvent(EventKind.SPEECH_END, 0),
        EndpointEvent(EventKind.DECISION_TICK, 200),
        EndpointEvent(EventKind.GENERATION_READY, 210),
    ):
        engine.handle(event)
    assert engine.handle(EndpointEvent(EventKind.INTERRUPT, 220, 0.7)) is None
    engine.handle(EndpointEvent(EventKind.INTERRUPT, 221, 0.8))
    assert engine.state is DuplexState.BARGE_IN


def test_barge_in_recovery_flushes_partials_and_listens() -> None:
    from echoparley.duplex import DuplexEngine, DuplexState
    from echoparley.events import EndpointEvent, EventKind

    engine = DuplexEngine(state=DuplexState.BARGE_IN, partial_units=[1, 2])
    engine.handle(EndpointEvent(EventKind.DECISION_TICK, 1))
    assert engine.state is DuplexState.RECOVER and engine.partial_units == []
    engine.handle(EndpointEvent(EventKind.RECOVERY_COMPLETE, 2))
    assert engine.state is DuplexState.LISTEN
