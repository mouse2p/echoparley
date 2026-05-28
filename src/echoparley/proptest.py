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
                    break
        return PropertyFailure(cases.seed, index, value, minimal)
    return None


def stream_roundtrip_invariant(value: UnifiedStream) -> bool:
    """Check exact public mapping roundtrip for a generated stream."""
    from echoparley.stream import stream_from_mapping, stream_to_mapping

    return stream_from_mapping(stream_to_mapping(value)) == value


def session_roundtrip_invariant(value: tuple[SessionEvent, ...]) -> bool:
    """Check byte-stable encode/decode reconstruction for generated sessions."""
    from echoparley.session import decode_session, encode_session

    encoded = encode_session(value)
    return decode_session(encoded) == value and encode_session(decode_session(encoded)) == encoded


def legal_duplex_invariant(events: tuple[EndpointEvent, ...]) -> bool:
    """Check that SPEAK is entered only from TAKE_FLOOR for an event trace."""
    from echoparley.duplex import DuplexEngine, DuplexState

    engine = DuplexEngine()
    for event in events:
        previous = engine.state
        engine.handle(event)
        if engine.state is DuplexState.SPEAK and previous not in {
            DuplexState.SPEAK,
            DuplexState.TAKE_FLOOR,
        }:
            return False
    return True


def context_budget_invariant(turns: tuple[ConversationTurn, ...], budget: int) -> bool:
    """Check reported cost equals retained turns and never exceeds the cap."""
    from echoparley.context import select_context

    window = select_context(turns, budget)
    return (
        window.used_tokens == sum(turn.token_count for turn in window.turns)
        and window.used_tokens <= budget
    )


def shrink_endpoint_trace(
    events: tuple[EndpointEvent, ...],
) -> tuple[tuple[EndpointEvent, ...], ...]:
    """Remove event chunks while preserving each retained event timestamp."""
    return shrink_sequence(events)


def shrink_session(events: tuple[SessionEvent, ...]) -> tuple[tuple[SessionEvent, ...], ...]:
    """Remove chunks and renumber retained events for valid replay artifacts."""
    candidates = []
    for candidate in shrink_sequence(events):
        candidates.append(
            tuple(
                SessionEvent(index, item.time_ms, item.kind, item.payload)
                for index, item in enumerate(candidate)
            )
        )
    return tuple(candidates)


def shrink_stream(value: UnifiedStream) -> tuple[UnifiedStream, ...]:
    """Shrink token content while retaining policy and schema metadata."""
    return tuple(
        UnifiedStream(tokens, value.policy, value.schema_version)
        for tokens in shrink_sequence(value.tokens)
    )


@dataclass(frozen=True, slots=True)
class PropertyRun:
    """Summary of evaluated cases plus an optional minimized failure."""

    name: str
    seed: int
    checked: int
    failure: PropertyFailure[object] | None = None

    def __post_init__(self) -> None:
        if not self.name or self.seed < 0 or self.checked < 0:
            raise ValueError("property run fields are invalid")

    @property
    def passed(self) -> bool:
        return self.failure is None


def evaluate_property(
    name: str,
    cases: CaseSet[T],
    predicate: Callable[[T], bool],
    shrinker: Callable[[T], tuple[T, ...]] | None = None,
) -> PropertyRun:
    """Evaluate a named property and report how many cases reached the failure."""
    if not name:
        raise ValueError("property name cannot be empty")
    failure = check_cases(cases, predicate, shrinker)
    checked = len(cases.values) if failure is None else failure.case_index + 1
    return PropertyRun(name, cases.seed, checked, failure)


def run_stream_suite(seed: int, count: int = 50) -> PropertyRun:
    """Evaluate exact mapping roundtrip across generated unified streams."""
    cases = generate_streams(seed, count)
    return evaluate_property("stream-roundtrip", cases, stream_roundtrip_invariant, shrink_stream)


def run_session_suite(seed: int, count: int = 50) -> PropertyRun:
    """Evaluate byte-identical replay across generated event sessions."""
    cases = generate_sessions(seed, count)
    return evaluate_property(
        "session-roundtrip", cases, session_roundtrip_invariant, shrink_session
    )


def run_duplex_suite(seed: int, count: int = 50) -> PropertyRun:
    """Evaluate legal state entry across generated endpoint traces."""
    cases = generate_endpoint_traces(seed, count)
    return evaluate_property(
        "duplex-legality", cases, legal_duplex_invariant, shrink_endpoint_trace
    )


def run_context_suite(seed: int, count: int = 30, maximum_budget: int = 32) -> PropertyRun:
    """Evaluate exact token accounting over generated histories and budgets."""
    histories = generate_turns(seed, count)
    cases = CaseSet(
        seed,
        tuple(
            (turns, budget) for turns in histories.values for budget in range(maximum_budget + 1)
        ),
    )
    return evaluate_property(
        "context-budget", cases, lambda item: context_budget_invariant(item[0], item[1])
    )


def property_suite_report(runs: tuple[PropertyRun, ...]) -> dict[str, object]:
    """Combine distinct executable property runs into a stable report."""
    names = tuple(run.name for run in runs)
    if not runs or len(names) != len(set(names)):
        raise ValueError("property suite report requires distinct runs")
    return {
        "schema_version": "1.0",
        "passed": all(run.passed for run in runs),
        "checked": sum(run.checked for run in runs),
        "runs": [
            {"name": run.name, "seed": run.seed, "checked": run.checked, "passed": run.passed}
            for run in runs
        ],
    }
