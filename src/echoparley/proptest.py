"""Small seeded property helpers tailored to echoparley data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CaseSet(Generic[T]):
    """Generated values together with the seed needed to reproduce them."""

    seed: int
    values: tuple[T, ...]

    def __post_init__(self) -> None:
        if self.seed < 0 or not self.values:
            raise ValueError("property cases require a non-negative seed and values")
