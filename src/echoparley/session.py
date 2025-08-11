"""Checksummed event sessions with exact deterministic replay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from echoparley.artifacts import ArtifactEnvelope, bytes_checksum, decode_jsonl, encode_jsonl


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


def encode_session(events: tuple[SessionEvent, ...]) -> bytes:
    envelopes = [
        ArtifactEnvelope.create(
            "session-event",
            {
                "sequence": event.sequence,
                "time_ms": event.time_ms,
                "kind": event.kind,
                "payload": event.payload,
            },
        )
        for event in events
    ]
    return encode_jsonl(envelopes)


def decode_session(data: bytes) -> tuple[SessionEvent, ...]:
    envelopes = decode_jsonl(data)
    events = tuple(
        SessionEvent(**envelope.payload)
        for envelope in envelopes
        if envelope.kind == "session-event"
    )
    if len(events) != len(envelopes) or any(
        event.sequence != index for index, event in enumerate(events)
    ):
        raise ValueError("session requires contiguous session-event sequences")
    return events


def session_digest(events: tuple[SessionEvent, ...]) -> str:
    """Hash the exact canonical replay bytes."""
    return bytes_checksum(encode_session(events))


@dataclass(slots=True)
class SessionReplayer:
    events: tuple[SessionEvent, ...]
    cursor: int = 0

    def next(self) -> SessionEvent:
        if self.cursor >= len(self.events):
            raise StopIteration("session replay exhausted")
        event = self.events[self.cursor]
        self.cursor += 1
        return event

    def seek(self, sequence: int) -> None:
        if not 0 <= sequence <= len(self.events):
            raise IndexError("replay sequence outside session")
        self.cursor = sequence


@dataclass(frozen=True, slots=True)
class SessionDifference:
    sequence: int
    left: SessionEvent | None
    right: SessionEvent | None


def diff_sessions(
    left: tuple[SessionEvent, ...], right: tuple[SessionEvent, ...]
) -> tuple[SessionDifference, ...]:
    """Return event-exact differences including missing tails."""
    differences: list[SessionDifference] = []
    for index in range(max(len(left), len(right))):
        left_event = left[index] if index < len(left) else None
        right_event = right[index] if index < len(right) else None
        if left_event != right_event:
            differences.append(SessionDifference(index, left_event, right_event))
    return tuple(differences)
