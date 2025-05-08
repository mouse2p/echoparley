"""Deterministic BPE-style text tokenization for synthetic transcripts."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


def normalize_text(text: str, *, lowercase: bool = True) -> str:
    """Apply NFKC, optional case folding, and canonical whitespace."""
    value = unicodedata.normalize("NFKC", text)
    if lowercase:
        value = value.casefold()
    return " ".join(value.split())


@dataclass(frozen=True, slots=True)
class BPEModel:
    """An ordered tuple of adjacent-symbol merges."""

    merges: tuple[tuple[str, str], ...]
    end_of_word: str = "</w>"

    def __post_init__(self) -> None:
        if not self.end_of_word or any(not left or not right for left, right in self.merges):
            raise ValueError("BPE symbols cannot be empty")
        if len(set(self.merges)) != len(self.merges):
            raise ValueError("BPE merges must be unique")
