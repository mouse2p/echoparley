"""Small seeded property helpers tailored to echoparley data structures."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from echoparley.events import EndpointEvent, EventKind
from echoparley.session import SessionEvent
from echoparley.state import ConversationTurn
from echoparley.stream import StreamToken, TokenKind, UnifiedStream

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CaseSet(Generic[T]):
    """Generated values together with the seed needed to reproduce them."""

    seed: int
    values: tuple[T, ...]

    def __post_init__(self) -> None:
        if self.seed < 0 or not self.values:
            raise ValueError("property cases require a non-negative seed and values")


def generate_streams(seed: int, count: int = 20) -> CaseSet[UnifiedStream]:
    """Generate valid time-aligned streams with mixed token namespaces."""
    if seed < 0 or count <= 0:
        raise ValueError("stream generator configuration is invalid")
    rng = random.Random(seed)
    streams = []
    spellings = {TokenKind.TEXT: "word", TokenKind.UNIT: "<unit:3>", TokenKind.CONTROL: "<silence>"}
    for _ in range(count):
        time_ms = 0
        tokens = []
        for _ in range(rng.randint(1, 8)):
            kind = rng.choice(list(TokenKind))
            duration = rng.randint(0, 40)
            tokens.append(
                StreamToken(
                    kind, spellings[kind], rng.choice(("a", "b")), time_ms, time_ms + duration
                )
            )
            time_ms += rng.randint(0, 30)
        streams.append(UnifiedStream(tuple(tokens), "time-aligned"))
    return CaseSet(seed, tuple(streams))


def generate_turns(seed: int, count: int = 20) -> CaseSet[tuple[ConversationTurn, ...]]:
    """Generate histories with planted topics and exact token costs."""
    if seed < 0 or count <= 0:
        raise ValueError("turn generator configuration is invalid")
    rng = random.Random(seed)
    histories = []
    for _ in range(count):
        time_ms = 0
        turns = []
        for index in range(rng.randint(1, 10)):
            duration = rng.randint(1, 200)
            turns.append(
                ConversationTurn(
                    ("a", "b")[index % 2],
                    f"turn-{index}",
                    rng.randint(0, 12),
                    time_ms,
                    time_ms + duration,
                    rng.choice(("alpha", "beta")),
                )
            )
            time_ms += duration + rng.randint(0, 50)
        histories.append(tuple(turns))
    return CaseSet(seed, tuple(histories))


def generate_sessions(seed: int, count: int = 20) -> CaseSet[tuple[SessionEvent, ...]]:
    """Generate contiguous, monotone session traces for replay properties."""
    if seed < 0 or count <= 0:
        raise ValueError("session generator configuration is invalid")
    rng = random.Random(seed)
    sessions = []
    for _ in range(count):
        now = 0
        events = []
        for sequence in range(rng.randint(1, 12)):
            now += rng.randint(0, 30)
            events.append(
                SessionEvent(
                    sequence,
                    now,
                    rng.choice(("tick", "observe", "act")),
                    {"value": rng.randint(0, 9)},
                )
            )
        sessions.append(tuple(events))
    return CaseSet(seed, tuple(sessions))


def generate_endpoint_traces(seed: int, count: int = 20) -> CaseSet[tuple[EndpointEvent, ...]]:
    """Generate chronological endpoint evidence for state-machine properties."""
    if seed < 0 or count <= 0:
        raise ValueError("endpoint generator configuration is invalid")
    rng = random.Random(seed)
    traces = []
    for _ in range(count):
        now = 0
        events = []
        for _ in range(rng.randint(1, 20)):
            now += rng.randint(0, 20)
            events.append(
                EndpointEvent(
                    rng.choice(list(EventKind)), now, rng.random(), rng.choice(("a", "b"))
                )
            )
        traces.append(tuple(events))
    return CaseSet(seed, tuple(traces))


def shrink_non_negative(value: int) -> tuple[int, ...]:
    """Return deterministic candidates approaching the minimal value zero."""
    if value < 0:
        raise ValueError("integer shrinker accepts only non-negative values")
    candidates = {0}
    current = value
    while current > 1:
        current //= 2
        candidates.add(current)
    candidates.discard(value)
    return tuple(sorted(candidates))


def shrink_sequence(values: tuple[T, ...]) -> tuple[tuple[T, ...], ...]:
    """Generate ordered chunk removals, from coarse halves to single items."""
    if not values:
        return ()
    candidates: list[tuple[T, ...]] = [()]
    width = max(1, len(values) // 2)
    while width:
        for start in range(0, len(values), width):
            candidate = values[:start] + values[start + width :]
            if candidate not in candidates and candidate != values:
                candidates.append(candidate)
        if width == 1:
            break
        width //= 2
    return tuple(candidates)


@dataclass(frozen=True, slots=True)
class PropertyFailure(Generic[T]):
    seed: int
    case_index: int
    original: T
    minimal: T


def check_cases(
    cases: CaseSet[T],
    predicate: Callable[[T], bool],
    shrinker: Callable[[T], tuple[T, ...]] | None = None,
) -> PropertyFailure[T] | None:
    """Return the first failing case and greedily minimized reproduction."""
    for index, value in enumerate(cases.values):
        if predicate(value):
            continue
        minimal = value
        if shrinker is not None:
            for candidate in shrinker(value):
                if not predicate(candidate):
                    minimal = candidate
        return PropertyFailure(cases.seed, index, value, minimal)
    return None
