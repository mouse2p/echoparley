"""Transparent topic tracking for planted synthetic transcripts."""

from __future__ import annotations

from dataclasses import dataclass

from echoparley.text import normalize_text


@dataclass(frozen=True, slots=True)
class TopicTracker:
    lexicon: dict[str, frozenset[str]]

    def predict(self, text: str) -> tuple[str, ...]:
        words = set(normalize_text(text).split())
        return tuple(sorted(topic for topic, cues in self.lexicon.items() if words & cues))

    def __post_init__(self) -> None:
        if not self.lexicon or any(not topic or not cues for topic, cues in self.lexicon.items()):
            raise ValueError("topic lexicon requires named topics with cues")
