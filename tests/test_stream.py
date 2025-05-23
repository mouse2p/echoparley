from __future__ import annotations

import pytest

from echoparley import stream


def test_timed_token_accepts_zero_duration_control() -> None:
    token = stream.StreamToken(stream.TokenKind.CONTROL, "<turn_start>", "a", 10, 10)
    assert token.start_ms == token.end_ms


def test_timed_token_rejects_backwards_interval() -> None:
    with pytest.raises(ValueError, match="invalid"):
        stream.StreamToken(stream.TokenKind.TEXT, "hello", "a", 2, 1)


@pytest.mark.parametrize(
    "kind,value",
    [
        (stream.TokenKind.UNIT, "word"),
        (stream.TokenKind.TEXT, "<unit:2>"),
        (stream.TokenKind.CONTROL, "hello"),
    ],
)
def test_token_namespace_rejects_mismatches(kind: stream.TokenKind, value: str) -> None:
    with pytest.raises(ValueError, match="namespace"):
        stream.validate_token_namespace(stream.StreamToken(kind, value, "a", 0, 1))
