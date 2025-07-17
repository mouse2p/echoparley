"""Explicit perception-to-first-unit latency accounting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TurnLatency:
    perception_ms: int
    decision_ms: int
    first_unit_ms: int

    def __post_init__(self) -> None:
        if (
            self.perception_ms < 0
            or not self.perception_ms <= self.decision_ms <= self.first_unit_ms
        ):
            raise ValueError("latency stages must be non-negative and ordered")

    @property
    def decision_delay_ms(self) -> int:
        return self.decision_ms - self.perception_ms

    @property
    def first_unit_delay_ms(self) -> int:
        return self.first_unit_ms - self.perception_ms
