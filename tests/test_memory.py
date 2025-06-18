import pytest

from echoparley.memory import dump_memory, load_memory
from echoparley.state import ConversationState, ConversationTurn


def test_memory_roundtrip_is_byte_stable() -> None:
    value = ConversationState(
        (ConversationTurn("a", "hi", 1, 0, 2, "greeting"),), ("greeting",), ("answer",)
    )
    encoded = dump_memory(value)
    assert load_memory(encoded) == value
    assert dump_memory(load_memory(encoded)) == encoded


def test_memory_detects_checksum_corruption() -> None:
    encoded = dump_memory(ConversationState())
    with pytest.raises(ValueError, match="line 1"):
        load_memory(encoded.replace(b"conversation-memory", b"conversation-memXry"))
