"""Accelerated two-party simulation over planted synthetic dialogues."""

from __future__ import annotations

from dataclasses import dataclass

from echoparley.duplex import DuplexState
from echoparley.latency import TurnLatency


@dataclass(frozen=True, slots=True)
class TraceEvent:
    time_ms: int
    agent: str
    state: DuplexState
    source: str


@dataclass(frozen=True, slots=True)
class SimulationResult:
    trace: tuple[TraceEvent, ...]
    latencies: tuple[TurnLatency, ...]
    planted_boundaries_ms: tuple[int, ...]
