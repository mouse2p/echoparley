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


def test_stream_mapping_roundtrip_is_exact() -> None:
    original = stream.UnifiedStream(
        (stream.StreamToken(stream.TokenKind.UNIT, "<unit:2>", "a", 1, 2),), "strict-turn"
    )
    mapping = stream.stream_to_mapping(original)
    assert mapping == {
        "schema_version": "1.0",
        "policy": "strict-turn",
        "tokens": [
            {"kind": "unit", "value": "<unit:2>", "speaker": "a", "start_ms": 1, "end_ms": 2}
        ],
    }
    assert stream.stream_from_mapping(mapping) == original


def test_bounded_turn_uses_content_extents() -> None:
    content = (stream.StreamToken(stream.TokenKind.TEXT, "hello", "a", 20, 40),)
    bounded = stream.bound_turn(content, "a")
    assert [token.value for token in bounded] == ["<turn_start>", "hello", "<turn_end>"]
    assert [(token.start_ms, token.end_ms) for token in bounded] == [(20, 20), (20, 40), (40, 40)]
