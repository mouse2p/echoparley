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


@dataclass(frozen=True, slots=True)
class TopicScores:
    precision: float
    recall: float


def topic_scores(predicted: tuple[str, ...], planted: tuple[str, ...]) -> TopicScores:
    """Score topic labels with defined empty-set behavior."""
    predicted_set, planted_set = set(predicted), set(planted)
    correct = len(predicted_set & planted_set)
    precision = correct / len(predicted_set) if predicted_set else float(not planted_set)
    recall = correct / len(planted_set) if planted_set else 1.0
    return TopicScores(round(precision, 6), round(recall, 6))
