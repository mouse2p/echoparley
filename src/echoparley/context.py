"""Deterministic token-budget context selection."""

from __future__ import annotations

from dataclasses import dataclass

from echoparley.state import ConversationTurn


@dataclass(frozen=True, slots=True)
class ContextWindow:
    turns: tuple[ConversationTurn, ...]
    used_tokens: int
    evicted_turns: int


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
