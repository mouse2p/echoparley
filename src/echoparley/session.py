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


@dataclass(slots=True)
class SessionRecorder:
    """Assign monotonic sequences while retaining clean partial sessions."""

    events: list[SessionEvent]
    closed: bool = False

    def __init__(self) -> None:
        self.events = []
        self.closed = False

    def append(
        self, time_ms: int, kind: str, payload: dict[str, Any] | None = None
    ) -> SessionEvent:
        if self.closed:
            raise RuntimeError("session recorder is closed")
        if self.events and time_ms < self.events[-1].time_ms:
            raise ValueError("session time cannot move backwards")
        event = SessionEvent(len(self.events), time_ms, kind, dict(payload or {}))
        self.events.append(event)
        return event

    def close(self) -> tuple[SessionEvent, ...]:
        self.closed = True
        return tuple(self.events)
