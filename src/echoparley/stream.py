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
