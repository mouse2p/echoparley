"""Small reproducible performance harness with deliberately loose guards."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BenchmarkSample:
    case: str
    repeat: int
    elapsed_ms: float
    work_seconds: float | None = None

    def __post_init__(self) -> None:
        if not self.case or self.repeat < 0 or self.elapsed_ms < 0:
            raise ValueError("benchmark sample fields are invalid")
        if self.work_seconds is not None and self.work_seconds <= 0:
            raise ValueError("benchmark work duration must be positive")

    @property
    def real_time_factor(self) -> float | None:
        if self.work_seconds is None:
            return None
        return round(self.elapsed_ms / 1000 / self.work_seconds, 6)
