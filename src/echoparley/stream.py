"""Versioned text, speech-unit, and turn-control token streams."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TokenKind(StrEnum):
    TEXT = "text"
    UNIT = "unit"
    CONTROL = "control"


@dataclass(frozen=True, slots=True)
class StreamToken:
    kind: TokenKind
    value: str
    speaker: str
    start_ms: int
    end_ms: int

    def __post_init__(self) -> None:
        if not self.value or not self.speaker or self.start_ms < 0 or self.end_ms < self.start_ms:
            raise ValueError("stream token has invalid value, speaker, or interval")


@dataclass(frozen=True, slots=True)
class UnifiedStream:
    tokens: tuple[StreamToken, ...]
    policy: str
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.policy or self.schema_version != "1.0":
            raise ValueError("unsupported stream policy or schema")


def validate_token_namespace(token: StreamToken) -> None:
    """Ensure textual spellings agree with the declared token kind."""
    is_unit = token.value.startswith("<unit:") and token.value.endswith(">")
    is_control = token.value.startswith("<") and token.value.endswith(">") and not is_unit
    expected = {
        TokenKind.UNIT: is_unit,
        TokenKind.CONTROL: is_control,
        TokenKind.TEXT: not (is_unit or is_control),
    }
    if not expected[token.kind]:
        raise ValueError(f"token spelling does not match {token.kind.value} namespace")


def stream_to_mapping(value: UnifiedStream) -> dict[str, object]:
    """Convert a unified stream to its complete schema mapping."""
    return {
        "schema_version": value.schema_version,
        "policy": value.policy,
        "tokens": [
            {
                "kind": token.kind.value,
                "value": token.value,
                "speaker": token.speaker,
                "start_ms": token.start_ms,
                "end_ms": token.end_ms,
            }
            for token in value.tokens
        ],
    }


def stream_from_mapping(value: dict[str, object]) -> UnifiedStream:
    """Restore a stream from a trusted JSON-compatible mapping."""
    if value.keys() != {"schema_version", "policy", "tokens"}:
        raise ValueError("stream fields do not match schema")
    tokens = tuple(
        StreamToken(
            TokenKind(item["kind"]),
            str(item["value"]),
            str(item["speaker"]),
            int(item["start_ms"]),
            int(item["end_ms"]),
        )
        for item in value["tokens"]  # type: ignore[union-attr]
    )
    for token in tokens:
        validate_token_namespace(token)
    return UnifiedStream(tokens, str(value["policy"]), str(value["schema_version"]))


def bound_turn(tokens: tuple[StreamToken, ...], speaker: str) -> tuple[StreamToken, ...]:
    """Wrap content with zero-duration start and end controls."""
    if not tokens or any(token.speaker != speaker for token in tokens):
        raise ValueError("bounded turn requires nonempty single-speaker content")
    start = min(token.start_ms for token in tokens)
    end = max(token.end_ms for token in tokens)
    return (
        StreamToken(TokenKind.CONTROL, "<turn_start>", speaker, start, start),
        *tokens,
        StreamToken(TokenKind.CONTROL, "<turn_end>", speaker, end, end),
    )


def strict_turn_interleave(turns: tuple[tuple[StreamToken, ...], ...]) -> UnifiedStream:
    """Order whole turns by their first timestamp without mixing content."""
    ordered = sorted(
        turns, key=lambda group: (group[0].start_ms, group[0].speaker) if group else (0, "")
    )
    flattened: list[StreamToken] = []
    for group in ordered:
        if group:
            flattened.extend(bound_turn(group, group[0].speaker))
    return UnifiedStream(tuple(flattened), "strict-turn")


def time_aligned_interleave(tokens: tuple[StreamToken, ...]) -> UnifiedStream:
    """Sort individual tokens using deterministic timestamp and namespace ties."""
    priority = {TokenKind.CONTROL: 0, TokenKind.TEXT: 1, TokenKind.UNIT: 2}
    ordered = sorted(
        tokens, key=lambda token: (token.start_ms, priority[token.kind], token.speaker, token.value)
    )
    return UnifiedStream(tuple(ordered), "time-aligned")


def dense_interleave(
    text_tokens: tuple[StreamToken, ...], unit_tokens: tuple[StreamToken, ...], cadence: int = 2
) -> UnifiedStream:
    """Emit a text token after each fixed number of units, then drain either side."""
    if cadence <= 0:
        raise ValueError("dense cadence must be positive")
    output: list[StreamToken] = []
    text_index = 0
    for unit_index, token in enumerate(unit_tokens, 1):
        output.append(token)
        if unit_index % cadence == 0 and text_index < len(text_tokens):
            output.append(text_tokens[text_index])
            text_index += 1
    output.extend(text_tokens[text_index:])
    return UnifiedStream(tuple(output), f"dense-interleave/v1?cadence={cadence}")
