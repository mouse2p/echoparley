"""Deterministic BPE-style text tokenization for synthetic transcripts."""

from __future__ import annotations

import unicodedata


def normalize_text(text: str, *, lowercase: bool = True) -> str:
    """Apply NFKC, optional case folding, and canonical whitespace."""
    value = unicodedata.normalize("NFKC", text)
    if lowercase:
        value = value.casefold()
    return " ".join(value.split())
