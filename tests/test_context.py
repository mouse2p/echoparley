from echoparley.context import ContextWindow, select_context
from echoparley.state import ConversationTurn


def test_context_keeps_newest_complete_suffix() -> None:
    turns = tuple(
        ConversationTurn("a", str(index), cost, index, index + 1)
        for index, cost in enumerate((2, 3, 4))
    )
    assert select_context(turns, 7) == ContextWindow(turns[1:], 7, 1)
    assert select_context(turns, 0) == ContextWindow((), 0, 3)


def test_oversized_newest_turn_evicts_everything() -> None:
    turns = (ConversationTurn("a", "large", 9, 0, 1),)
    assert select_context(turns, 8) == ContextWindow((), 0, 1)


def test_response_reserve_reduces_history_budget() -> None:
    from echoparley.context import select_context_with_reserve

    turns = (ConversationTurn("a", "one", 4, 0, 1), ConversationTurn("b", "two", 4, 2, 3))
    assert select_context_with_reserve(turns, 10, 2).turns == turns
    assert select_context_with_reserve(turns, 10, 3).turns == (turns[-1],)


def test_context_policy_names_are_stable_and_validated() -> None:
    import pytest

    from echoparley.context import EvictionPolicy, parse_eviction_policy

    assert parse_eviction_policy("salience") is EvictionPolicy.SALIENCE
    with pytest.raises(ValueError, match="recency, turn-boundary, salience"):
        parse_eviction_policy("oldest")


def test_policy_interface_matches_recency_selection() -> None:
    from echoparley.context import select_context_by_policy

    turns = (ConversationTurn("a", "one", 2, 0, 1), ConversationTurn("b", "two", 3, 2, 3))
    assert select_context_by_policy(turns, 3, "recency") == select_context(turns, 3)


def test_boundary_policy_never_splits_a_topic_segment() -> None:
    from echoparley.context import select_context_by_policy, select_turn_boundary_context

    turns = (
        ConversationTurn("a", "old", 2, 0, 1, "old"),
        ConversationTurn("b", "new one", 3, 2, 3, "new"),
        ConversationTurn("a", "new two", 3, 4, 5, "new"),
    )
    assert select_turn_boundary_context(turns, 5).turns == ()
    assert select_turn_boundary_context(turns, 6).turns == turns[1:]
    assert select_context_by_policy(turns, 6, "turn-boundary").turns == turns[1:]
