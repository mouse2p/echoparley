import pytest

from echoparley.runtime import TickConfig


def test_tick_config_defaults_to_accelerated_time() -> None:
    assert TickConfig() == TickConfig(20, True)
    with pytest.raises(ValueError, match="positive"):
        TickConfig(0)


def test_cancellation_token_records_reason() -> None:
    from echoparley.runtime import CancellationToken

    token = CancellationToken()
    token.cancel("user-stop")
    assert token.cancelled and token.reason == "user-stop"


def test_tick_loop_stops_after_callback_cancellation() -> None:
    from echoparley.runtime import CancellationToken, run_ticks

    token = CancellationToken()
    observed: list[int] = []

    def callback(time_ms: int) -> None:
        observed.append(time_ms)
        if time_ms == 20:
            token.cancel("done")

    assert run_ticks(10, callback, cancellation=token) == (0, 20)
    assert observed == [0, 20]


def test_recorded_ticks_have_contiguous_sequences() -> None:
    from echoparley.runtime import TickConfig, record_ticks

    events = record_ticks(3, TickConfig(5))
    assert [(event.sequence, event.time_ms) for event in events] == [(0, 0), (1, 5), (2, 10)]
