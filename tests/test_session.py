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


def test_session_serialization_is_byte_stable() -> None:
    from echoparley.session import decode_session, encode_session

    events = (SessionEvent(0, 4, "unit", {"id": 3}),)
    encoded = encode_session(events)
    assert decode_session(encoded) == events
    assert encode_session(decode_session(encoded)) == encoded


def test_session_replayer_supports_exact_seek() -> None:
    from echoparley.session import SessionReplayer

    events = (SessionEvent(0, 0, "a", {}), SessionEvent(1, 1, "b", {}))
    replay = SessionReplayer(events)
    replay.seek(1)
    assert replay.next() == events[1]
    with pytest.raises(StopIteration, match="exhausted"):
        replay.next()


def test_session_diff_reports_changes_and_missing_tails() -> None:
    from echoparley.session import diff_sessions

    left = (SessionEvent(0, 0, "a", {}), SessionEvent(1, 1, "b", {}))
    right = (SessionEvent(0, 0, "changed", {}),)
    differences = diff_sessions(left, right)
    assert [item.sequence for item in differences] == [0, 1]
    assert differences[1].right is None


def test_session_difference_kinds_follow_left_to_right_operations() -> None:
    from echoparley.session import DifferenceKind, SessionDifference, difference_kind

    event = SessionEvent(0, 0, "tick", {})
    changed = SessionEvent(0, 1, "tick", {})
    assert difference_kind(SessionDifference(0, None, event)) is DifferenceKind.INSERT
    assert difference_kind(SessionDifference(0, event, None)) is DifferenceKind.DELETE
    assert difference_kind(SessionDifference(0, event, changed)) is DifferenceKind.CHANGE


def test_session_digest_changes_with_payload() -> None:
    from echoparley.session import session_digest

    first = (SessionEvent(0, 0, "unit", {"id": 1}),)
    second = (SessionEvent(0, 0, "unit", {"id": 2}),)
    assert session_digest(first) != session_digest(second)


def test_session_encoder_rejects_sequence_gaps() -> None:
    from echoparley.session import encode_session

    with pytest.raises(ValueError, match="contiguous"):
        encode_session((SessionEvent(1, 0, "gap", {}),))
