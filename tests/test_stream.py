from __future__ import annotations

import pytest

from echoparley import stream


def test_timed_token_accepts_zero_duration_control() -> None:
    token = stream.StreamToken(stream.TokenKind.CONTROL, "<turn_start>", "a", 10, 10)
    assert token.start_ms == token.end_ms


def test_timed_token_rejects_backwards_interval() -> None:
    with pytest.raises(ValueError, match="invalid"):
        stream.StreamToken(stream.TokenKind.TEXT, "hello", "a", 2, 1)
