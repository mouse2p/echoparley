"""Cancellable wall-clock or accelerated session tick loops."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TickConfig:
    interval_ms: int = 20
    accelerated: bool = True

    def __post_init__(self) -> None:
        if self.interval_ms <= 0:
            raise ValueError("tick interval must be positive")
