"""Pluggable offline, replay, and local-loopback dialogue adapters."""

from __future__ import annotations

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
