"""Checksummed conversation-state persistence."""

from __future__ import annotations

from echoparley.artifacts import ArtifactEnvelope, decode_jsonl, encode_jsonl
from echoparley.state import ConversationState, ConversationTurn


def dump_memory(value: ConversationState) -> bytes:
    """Encode one conversation state in a checksummed JSONL envelope."""
    payload = {
        "topics": list(value.topic_stack),
        "pending_acts": list(value.pending_acts),
        "turns": [
            {
                "speaker": turn.speaker,
                "text": turn.text,
                "token_count": turn.token_count,
                "start_ms": turn.start_ms,
                "end_ms": turn.end_ms,
                "topic": turn.topic,
            }
            for turn in value.turns
        ],
    }
    return encode_jsonl([ArtifactEnvelope.create("conversation-memory", payload)])


def load_memory(data: bytes) -> ConversationState:
    """Decode exactly one verified conversation-memory envelope."""
    envelopes = decode_jsonl(data)
    if len(envelopes) != 1 or envelopes[0].kind != "conversation-memory":
        raise ValueError("memory file must contain one conversation-memory artifact")
    payload = envelopes[0].payload
    turns = tuple(ConversationTurn(**item) for item in payload["turns"])
    return ConversationState(turns, tuple(payload["topics"]), tuple(payload["pending_acts"]))
