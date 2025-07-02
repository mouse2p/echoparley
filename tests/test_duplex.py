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
