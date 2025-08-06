import pytest

from echoparley.session import SessionEvent


def test_session_event_accepts_initial_sequence() -> None:
    assert SessionEvent(0, 0, "start", {}).sequence == 0


def test_session_event_rejects_negative_time() -> None:
    with pytest.raises(ValueError, match="invalid"):
        SessionEvent(0, -1, "tick", {})


def test_recorder_assigns_sequences_and_closes() -> None:
    from echoparley.session import SessionRecorder

    recorder = SessionRecorder()
    assert recorder.append(0, "start").sequence == 0
    assert recorder.append(2, "tick").sequence == 1
    assert len(recorder.close()) == 2
    with pytest.raises(RuntimeError, match="closed"):
        recorder.append(3, "late")
