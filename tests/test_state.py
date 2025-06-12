from __future__ import annotations

import pytest

from echoparley import state


def test_state_append_is_immutable_and_chronological() -> None:
    original = state.ConversationState()
    turn = state.ConversationTurn("a", "hello", 1, 5, 20)
    updated = original.append(turn)
    assert original.turns == () and updated.turns == (turn,)
    with pytest.raises(ValueError, match="chronological"):
        updated.append(state.ConversationTurn("b", "early", 1, 1, 2))


def test_topic_stack_is_last_in_first_out() -> None:
    stacked = state.ConversationState().push_topic("booking").push_topic("date")
    popped, topic = stacked.pop_topic()
    assert topic == "date" and popped.current_topic == "booking"
    with pytest.raises(IndexError, match="empty"):
        state.ConversationState().pop_topic()


def test_pending_acts_are_first_in_first_out() -> None:
    queued = state.ConversationState().enqueue_act("answer").enqueue_act("confirm")
    remaining, first = queued.dequeue_act()
    assert first == "answer" and remaining.pending_acts == ("confirm",)
