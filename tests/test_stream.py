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


def test_strict_turn_interleave_keeps_overlaps_atomic() -> None:
    late = (stream.StreamToken(stream.TokenKind.TEXT, "late", "b", 5, 9),)
    early = (stream.StreamToken(stream.TokenKind.TEXT, "early", "a", 0, 10),)
    result = stream.strict_turn_interleave((late, early))
    assert [token.value for token in result.tokens] == [
        "<turn_start>",
        "early",
        "<turn_end>",
        "<turn_start>",
        "late",
        "<turn_end>",
    ]


def test_time_aligned_interleave_has_stable_ties() -> None:
    tokens = (
        stream.StreamToken(stream.TokenKind.UNIT, "<unit:1>", "a", 0, 2),
        stream.StreamToken(stream.TokenKind.TEXT, "hi", "b", 0, 3),
        stream.StreamToken(stream.TokenKind.CONTROL, "<turn_start>", "a", 0, 0),
    )
    assert [token.kind for token in stream.time_aligned_interleave(tokens).tokens] == [
        stream.TokenKind.CONTROL,
        stream.TokenKind.TEXT,
        stream.TokenKind.UNIT,
    ]


def test_dense_interleave_respects_cadence_and_drains_text() -> None:
    units = tuple(
        stream.StreamToken(stream.TokenKind.UNIT, f"<unit:{index}>", "a", index, index + 1)
        for index in range(3)
    )
    texts = tuple(
        stream.StreamToken(stream.TokenKind.TEXT, word, "a", 0, 3) for word in ("one", "two")
    )
    result = stream.dense_interleave(texts, units, 2)
    assert [token.value for token in result.tokens] == [
        "<unit:0>",
        "<unit:1>",
        "one",
        "<unit:2>",
        "two",
    ]
    with pytest.raises(ValueError, match="cadence"):
        stream.dense_interleave((), (), 0)


def test_stream_split_preserves_each_namespace() -> None:
    tokens = (
        stream.StreamToken(stream.TokenKind.TEXT, "hi", "a", 0, 2),
        stream.StreamToken(stream.TokenKind.UNIT, "<unit:0>", "a", 0, 1),
        stream.StreamToken(stream.TokenKind.CONTROL, "<silence>", "a", 2, 3),
    )
    split = stream.split_stream(stream.time_aligned_interleave(tokens))
    assert split[stream.TokenKind.TEXT] == (tokens[0],)
    assert split[stream.TokenKind.UNIT] == (tokens[1],)
    assert split[stream.TokenKind.CONTROL] == (tokens[2],)
