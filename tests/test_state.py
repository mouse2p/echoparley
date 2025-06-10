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
