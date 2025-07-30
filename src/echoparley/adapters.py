"""Pluggable offline, replay, and local-loopback dialogue adapters."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from echoparley.events import EndpointEvent
from echoparley.stream import UnifiedStream


@dataclass(frozen=True, slots=True)
class AdapterAction:
    tokens: tuple[str, ...]
    delay_ms: int = 0
    finished: bool = True

    def __post_init__(self) -> None:
        if self.delay_ms < 0:
            raise ValueError("adapter delay must be non-negative")


class DialogueAdapter(Protocol):
    def observe(self, value: UnifiedStream) -> None: ...

    def act(self, events: tuple[EndpointEvent, ...]) -> AdapterAction: ...


@dataclass(slots=True)
class ScriptedAdapter:
    """Return declared actions in order for deterministic offline tests."""

    actions: tuple[AdapterAction, ...]
    cursor: int = 0
    observations: tuple[UnifiedStream, ...] = ()

    def observe(self, value: UnifiedStream) -> None:
        self.observations = (*self.observations, value)

    def act(self, events: tuple[EndpointEvent, ...]) -> AdapterAction:
        del events
        if self.cursor >= len(self.actions):
            raise StopIteration("scripted adapter exhausted")
        action = self.actions[self.cursor]
        self.cursor += 1
        return action

    def reset(self) -> None:
        """Rewind actions and clear observations for a fresh replay."""
        self.cursor = 0
        self.observations = ()


@dataclass(slots=True)
class ReplayAdapter:
    """Replay validated action mappings without generating new content."""

    records: tuple[dict[str, object], ...]
    cursor: int = 0

    def observe(self, value: UnifiedStream) -> None:
        del value

    def act(self, events: tuple[EndpointEvent, ...]) -> AdapterAction:
        del events
        if self.cursor >= len(self.records):
            raise StopIteration("replay adapter exhausted")
        record = self.records[self.cursor]
        self.cursor += 1
        if record.keys() != {"tokens", "delay_ms", "finished"}:
            raise ValueError("replay action fields do not match schema")
        return AdapterAction(
            tuple(str(token) for token in record["tokens"]),
            int(record["delay_ms"]),
            bool(record["finished"]),
        )  # type: ignore[union-attr]


@dataclass(slots=True)
class LoopbackHTTPAdapter:
    """HTTP adapter restricted to an explicit local mock endpoint."""

    url: str
    timeout_seconds: float = 1.0
    observed_tokens: int = 0

    def __post_init__(self) -> None:
        if not (
            self.url.startswith("http://127.0.0.1:") or self.url.startswith("http://localhost:")
        ):
            raise ValueError("loopback adapter only permits local mock HTTP endpoints")

    def observe(self, value: UnifiedStream) -> None:
        self.observed_tokens += len(value.tokens)

    def act(self, events: tuple[EndpointEvent, ...]) -> AdapterAction:
        payload = json.dumps(
            {"event_count": len(events), "observed_tokens": self.observed_tokens}
        ).encode()
        request = urllib.request.Request(self.url, payload, {"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            result = json.loads(response.read())
        return AdapterAction(
            tuple(result["tokens"]),
            int(result.get("delay_ms", 0)),
            bool(result.get("finished", True)),
        )
