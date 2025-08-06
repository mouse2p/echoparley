import pytest

from echoparley.session import SessionEvent


def test_session_event_accepts_initial_sequence() -> None:
    assert SessionEvent(0, 0, "start", {}).sequence == 0


def test_session_event_rejects_negative_time() -> None:
    with pytest.raises(ValueError, match="invalid"):
        SessionEvent(0, -1, "tick", {})
