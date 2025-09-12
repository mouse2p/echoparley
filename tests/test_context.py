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


def test_salience_policy_retains_important_old_turns_in_order() -> None:
    from echoparley.context import select_salient_context

    turns = tuple(ConversationTurn("a", str(i), 2, i, i + 1) for i in range(3))
    window = select_salient_context(turns, 4, (1.0, 0.1, 0.9))
    assert window.turns == (turns[0], turns[2])
    assert window.used_tokens == 4


def test_salience_selection_is_deterministic_at_exact_budget() -> None:
    import pytest

    from echoparley.context import select_context_by_policy, select_salient_context

    turns = tuple(ConversationTurn("a", str(i), i + 1, i, i + 1) for i in range(3))
    assert select_salient_context(turns, 3, (1.0, 1.0, 1.0)).turns == (turns[2],)
    with pytest.raises(ValueError, match="align"):
        select_salient_context(turns, 3, (1.0,))
    assert select_context_by_policy(
        turns, 3, "salience", salience_scores=(1.0, 1.0, 1.0)
    ).turns == (turns[2],)


def test_retention_score_counts_planted_relevant_topics() -> None:
    from echoparley.context import EvictionPolicy, context_retention_score

    turns = (
        ConversationTurn("a", "x", 2, 0, 1, "keep"),
        ConversationTurn("b", "y", 2, 2, 3, "drop"),
    )
    score = context_retention_score(
        ContextWindow(turns, 4, 0),
        EvictionPolicy.RECENCY,
        frozenset({"keep"}),
        total_relevant=2,
    )
    assert score.retained_relevant == 1 and score.recall == 0.5
