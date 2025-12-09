"""Small reproducible performance harness with deliberately loose guards."""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable
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


def run_benchmark(
    case: str,
    operation: Callable[[], object],
    *,
    warmup: int = 1,
    repeats: int = 5,
    work_seconds: float | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> tuple[BenchmarkSample, ...]:
    """Warm an operation, then measure repeats using an injectable clock."""
    if not case or warmup < 0 or repeats <= 0:
        raise ValueError("benchmark runner configuration is invalid")
    for _ in range(warmup):
        operation()
    samples = []
    for repeat in range(repeats):
        started = clock()
        operation()
        elapsed_ms = (clock() - started) * 1000
        samples.append(BenchmarkSample(case, repeat, round(elapsed_ms, 6), work_seconds))
    return tuple(samples)


@dataclass(frozen=True, slots=True)
class RegressionGuard:
    case: str
    upper_bound_ms: float

    def __post_init__(self) -> None:
        if not self.case or self.upper_bound_ms <= 0:
            raise ValueError("regression guard requires a case and positive bound")

    def assert_summary(self, summary: BenchmarkSummary) -> None:
        """Fail only when the measured mean exceeds a deliberately loose bound."""
        if summary.case != self.case:
            raise ValueError("regression guard case does not match summary")
        if summary.mean_ms > self.upper_bound_ms:
            raise AssertionError(
                f"{self.case} mean {summary.mean_ms} ms exceeded loose bound "
                f"{self.upper_bound_ms} ms"
            )
