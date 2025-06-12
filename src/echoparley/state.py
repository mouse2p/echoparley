"""Deterministic dialogue history, context, topics, and pending acts."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    speaker: str
    text: str
    token_count: int
    start_ms: int
    end_ms: int
    topic: str | None = None

    def __post_init__(self) -> None:
        if (
            not self.speaker
            or self.token_count < 0
            or self.start_ms < 0
            or self.end_ms < self.start_ms
        ):
            raise ValueError("invalid conversation turn")


@dataclass(frozen=True, slots=True)
class ConversationState:
    turns: tuple[ConversationTurn, ...] = ()
    topic_stack: tuple[str, ...] = ()
    pending_acts: tuple[str, ...] = ()

    def append(self, turn: ConversationTurn) -> ConversationState:
        if self.turns and turn.start_ms < self.turns[-1].start_ms:
            raise ValueError("turn history must be chronological")
        return replace(self, turns=(*self.turns, turn))

    def push_topic(self, topic: str) -> ConversationState:
        if not topic.strip():
            raise ValueError("topic cannot be blank")
        return replace(self, topic_stack=(*self.topic_stack, topic.strip()))

    def pop_topic(self) -> tuple[ConversationState, str]:
        if not self.topic_stack:
            raise IndexError("topic stack is empty")
        return replace(self, topic_stack=self.topic_stack[:-1]), self.topic_stack[-1]

    @property
    def current_topic(self) -> str | None:
        return self.topic_stack[-1] if self.topic_stack else None
