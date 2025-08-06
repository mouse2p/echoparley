"""Checksummed event sessions with exact deterministic replay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SessionEvent:
    sequence: int
    time_ms: int
    kind: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if self.sequence < 0 or self.time_ms < 0 or not self.kind:
            raise ValueError("session event fields are invalid")
