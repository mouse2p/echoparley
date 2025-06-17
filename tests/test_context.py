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
