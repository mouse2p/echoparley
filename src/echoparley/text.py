"""Deterministic BPE-style text tokenization for synthetic transcripts."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from itertools import pairwise


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


def _merge_pair(symbols: tuple[str, ...], pair: tuple[str, str]) -> tuple[str, ...]:
    output: list[str] = []
    index = 0
    while index < len(symbols):
        if index + 1 < len(symbols) and symbols[index : index + 2] == pair:
            output.append(pair[0] + pair[1])
            index += 2
        else:
            output.append(symbols[index])
            index += 1
    return tuple(output)


def train_bpe(corpus: list[str], merge_count: int, *, end_of_word: str = "</w>") -> BPEModel:
    """Train merges by frequency with lexical tie breaking."""
    if merge_count < 0 or not end_of_word:
        raise ValueError("merge_count must be non-negative and marker nonempty")
    words = [(*word, end_of_word) for item in corpus for word in normalize_text(item).split()]
    merges: list[tuple[str, str]] = []
    for _ in range(merge_count):
        counts: dict[tuple[str, str], int] = {}
        for symbols in words:
            for pair in pairwise(symbols):
                counts[pair] = counts.get(pair, 0) + 1
        if not counts:
            break
        best = min(counts, key=lambda pair: (-counts[pair], pair))
        merges.append(best)
        words = [_merge_pair(symbols, best) for symbols in words]
    return BPEModel(tuple(merges), end_of_word)


def encode_subwords(model: BPEModel, value: str) -> tuple[str, ...]:
    """Encode normalized words while keeping an explicit word boundary."""
    encoded: list[str] = []
    for word in normalize_text(value).split():
        symbols = (*word, model.end_of_word)
        for merge in model.merges:
            symbols = _merge_pair(symbols, merge)
        encoded.extend(symbols)
    return tuple(encoded)


def decode_subwords(model: BPEModel, tokens: tuple[str, ...]) -> str:
    """Decode tokens, rejecting streams without complete word markers."""
    text_value = "".join(tokens)
    if text_value and not text_value.endswith(model.end_of_word):
        raise ValueError("subword stream ends inside a word")
    words = text_value.split(model.end_of_word)
    return " ".join(words[:-1])
