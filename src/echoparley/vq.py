"""Codebook diagnostics and update mechanics for synthetic VQ experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class CodebookHealth:
    size: int
    occupied: int
    occupancy_ratio: float
    perplexity: float
    effective_size: float


def codebook_health(assignments: IntArray, size: int) -> CodebookHealth:
    """Measure occupancy and entropy without implying representation quality."""
    values = np.asarray(assignments, dtype=np.int64)
    if size <= 0 or values.ndim != 1 or np.any((values < 0) | (values >= size)):
        raise ValueError("assignments must be a vector inside the codebook")
    counts = np.bincount(values, minlength=size)
    probabilities = counts[counts > 0] / max(1, len(values))
    entropy = -float(np.sum(probabilities * np.log(probabilities))) if len(values) else 0.0
    perplexity = float(np.exp(entropy))
    occupied = int(np.count_nonzero(counts))
    return CodebookHealth(
        size, occupied, round(occupied / size, 6), round(perplexity, 6), round(perplexity / size, 6)
    )
