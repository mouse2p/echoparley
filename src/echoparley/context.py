"""Deterministic token-budget context selection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from echoparley.state import ConversationTurn


@dataclass(frozen=True, slots=True)
class ContextWindow:
    turns: tuple[ConversationTurn, ...]
    used_tokens: int
    evicted_turns: int


class EvictionPolicy(StrEnum):
    """Stable names for deterministic context-selection strategies."""

    RECENCY = "recency"
    TURN_BOUNDARY = "turn-boundary"
    SALIENCE = "salience"


def parse_eviction_policy(value: str) -> EvictionPolicy:
    """Parse a policy name with an actionable error for configuration surfaces."""
    try:
        return EvictionPolicy(value)
    except ValueError as error:
        choices = ", ".join(policy.value for policy in EvictionPolicy)
        raise ValueError(f"unknown eviction policy {value!r}; choose from {choices}") from error


def select_context(turns: tuple[ConversationTurn, ...], budget: int) -> ContextWindow:
    """Keep the newest complete turns that fit a non-negative budget."""
    if budget < 0:
        raise ValueError("context budget must be non-negative")
    selected: list[ConversationTurn] = []
    used = 0
    for turn in reversed(turns):
        if used + turn.token_count > budget:
            break
        selected.append(turn)
        used += turn.token_count
    selected.reverse()
    return ContextWindow(tuple(selected), used, len(turns) - len(selected))


def select_context_with_reserve(
    turns: tuple[ConversationTurn, ...], total_budget: int, response_reserve: int
) -> ContextWindow:
    """Select history after reserving capacity for a future response."""
    if response_reserve < 0 or response_reserve > total_budget:
        raise ValueError("response reserve must fit the total budget")
    return select_context(turns, total_budget - response_reserve)


def select_context_by_policy(
    turns: tuple[ConversationTurn, ...],
    budget: int,
    policy: EvictionPolicy | str = EvictionPolicy.RECENCY,
    *,
    salience_scores: tuple[float, ...] | None = None,
) -> ContextWindow:
    """Select context through a stable policy interface."""
    resolved = parse_eviction_policy(policy) if isinstance(policy, str) else policy
    if resolved is EvictionPolicy.RECENCY:
        return select_context(turns, budget)
    if resolved is EvictionPolicy.TURN_BOUNDARY:
        return select_turn_boundary_context(turns, budget)
    if resolved is EvictionPolicy.SALIENCE:
        if salience_scores is None:
            raise ValueError("salience policy requires scores")
        return select_salient_context(turns, budget, salience_scores)
    raise NotImplementedError(f"context policy {resolved.value!r} is not available yet")


def select_turn_boundary_context(turns: tuple[ConversationTurn, ...], budget: int) -> ContextWindow:
    """Keep newest complete contiguous topic segments without splitting one."""
    if budget < 0:
        raise ValueError("context budget must be non-negative")
    segments: list[tuple[ConversationTurn, ...]] = []
    for turn in turns:
        if not segments or segments[-1][-1].topic != turn.topic:
            segments.append((turn,))
        else:
            segments[-1] = (*segments[-1], turn)
    selected: list[ConversationTurn] = []
    used = 0
    for segment in reversed(segments):
        cost = sum(turn.token_count for turn in segment)
        if used + cost > budget:
            break
        selected[0:0] = segment
        used += cost
    return ContextWindow(tuple(selected), used, len(turns) - len(selected))


def select_salient_context(
    turns: tuple[ConversationTurn, ...], budget: int, scores: tuple[float, ...]
) -> ContextWindow:
    """Select high-scoring whole turns, breaking ties toward recent turns."""
    if budget < 0 or len(scores) != len(turns) or any(score < 0 for score in scores):
        raise ValueError("salience scores must align and budget must be non-negative")
    ranking = sorted(range(len(turns)), key=lambda index: (scores[index], index), reverse=True)
    chosen: set[int] = set()
    used = 0
    for index in ranking:
        cost = turns[index].token_count
        if used + cost <= budget:
            chosen.add(index)
            used += cost
    selected = tuple(turn for index, turn in enumerate(turns) if index in chosen)
    return ContextWindow(selected, used, len(turns) - len(selected))


@dataclass(frozen=True, slots=True)
class RetentionScore:
    policy: EvictionPolicy
    retained_relevant: int
    total_relevant: int
    used_tokens: int

    @property
    def recall(self) -> float:
        return (
            round(self.retained_relevant / self.total_relevant, 6) if self.total_relevant else 1.0
        )


def context_retention_score(
    window: ContextWindow,
    policy: EvictionPolicy,
    relevant_topics: frozenset[str],
    *,
    total_relevant: int | None = None,
) -> RetentionScore:
    """Score retained planted topics for policy comparisons."""
    relevant = sum(turn.topic in relevant_topics for turn in window.turns)
    total = relevant if total_relevant is None else total_relevant
    if total < relevant:
        raise ValueError("total relevant turns cannot be smaller than retained count")
    return RetentionScore(policy, relevant, total, window.used_tokens)


def planted_topic_salience(
    turns: tuple[ConversationTurn, ...], relevant_topics: frozenset[str]
) -> tuple[float, ...]:
    """Assign transparent salience using planted topic membership and recency."""
    total = max(1, len(turns))
    return tuple(
        round((1.0 if turn.topic in relevant_topics else 0.1) + index / total * 0.01, 6)
        for index, turn in enumerate(turns)
    )
