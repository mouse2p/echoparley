"""Small reproducible performance harness with deliberately loose guards."""

from __future__ import annotations

import statistics
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


@dataclass(frozen=True, slots=True)
class BenchmarkSummary:
    case: str
    repeats: int
    mean_ms: float
    median_ms: float
    p95_ms: float
    stdev_ms: float


def summarize_samples(samples: tuple[BenchmarkSample, ...]) -> BenchmarkSummary:
    """Summarize samples for one case with production-point rounding."""
    if not samples or len({sample.case for sample in samples}) != 1:
        raise ValueError("benchmark summary requires samples from one case")
    values = sorted(sample.elapsed_ms for sample in samples)
    rank = max(0, min(len(values) - 1, round(0.95 * (len(values) - 1))))
    return BenchmarkSummary(
        samples[0].case,
        len(values),
        round(statistics.fmean(values), 6),
        round(statistics.median(values), 6),
        round(values[rank], 6),
        round(statistics.stdev(values), 6) if len(values) > 1 else 0.0,
    )
