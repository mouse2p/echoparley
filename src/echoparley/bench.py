"""Small reproducible performance harness with deliberately loose guards."""

from __future__ import annotations

import platform
import statistics
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np

from echoparley import __version__
from echoparley.artifacts import ArtifactEnvelope, decode_jsonl, encode_jsonl
from echoparley.units import fit_unit_extractor


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


def encode_benchmark_jsonl(samples: tuple[BenchmarkSample, ...]) -> bytes:
    """Encode samples in the common checksummed artifact envelope."""
    return encode_jsonl(
        ArtifactEnvelope.create("benchmark-sample", asdict(sample), "1.0") for sample in samples
    )


def decode_benchmark_jsonl(data: bytes) -> tuple[BenchmarkSample, ...]:
    envelopes = decode_jsonl(data)
    if any(item.kind != "benchmark-sample" or item.schema_version != "1.0" for item in envelopes):
        raise ValueError("benchmark JSONL contains an unsupported artifact")
    return tuple(BenchmarkSample(**item.payload) for item in envelopes)


def benchmark_units(seed: int = 0, repeats: int = 3) -> tuple[BenchmarkSample, ...]:
    """Measure fitting and extraction over a small seeded synthetic matrix."""
    rng = np.random.default_rng(seed)
    features = rng.normal(size=(128, 8))

    def operation() -> None:
        extractor = fit_unit_extractor(features, 4, 8, seed=seed)
        extractor.extract(features)

    return run_benchmark("unit-extraction", operation, warmup=1, repeats=repeats, work_seconds=1.28)


def benchmark_streams(seed: int = 0, repeats: int = 3) -> tuple[BenchmarkSample, ...]:
    """Measure mapping roundtrips over generated deterministic streams."""
    from echoparley.proptest import generate_streams
    from echoparley.stream import stream_from_mapping, stream_to_mapping

    streams = generate_streams(seed, 64).values

    def operation() -> None:
        for stream in streams:
            stream_from_mapping(stream_to_mapping(stream))

    return run_benchmark("stream-roundtrip", operation, warmup=1, repeats=repeats)


def benchmark_simulator(seed: int = 0, repeats: int = 3) -> tuple[BenchmarkSample, ...]:
    """Measure deterministic synthetic dialogue simulation throughput."""
    from echoparley.simulator import simulate_dialogue
    from echoparley.synth import barge_in_scenario

    scenario = barge_in_scenario(seed)
    return run_benchmark(
        "simulator",
        lambda: simulate_dialogue(scenario),
        warmup=1,
        repeats=repeats,
        work_seconds=scenario.duration_ms / 1000,
    )


def benchmark_suite(seed: int = 0, repeats: int = 3) -> tuple[BenchmarkSample, ...]:
    """Run all offline cases with shared seed and repeat settings."""
    return (
        *benchmark_units(seed, repeats),
        *benchmark_streams(seed, repeats),
        *benchmark_simulator(seed, repeats),
    )


def benchmark_summaries(samples: tuple[BenchmarkSample, ...]) -> tuple[BenchmarkSummary, ...]:
    """Group suite samples by case in stable first-seen order."""
    cases = tuple(dict.fromkeys(sample.case for sample in samples))
    return tuple(
        summarize_samples(tuple(sample for sample in samples if sample.case == case))
        for case in cases
    )


@dataclass(frozen=True, slots=True)
class BenchmarkEnvironment:
    python: str
    numpy: str
    platform: str
    package: str


def benchmark_environment() -> BenchmarkEnvironment:
    """Capture versions needed to interpret machine-dependent measurements."""
    return BenchmarkEnvironment(
        platform.python_version(), np.__version__, platform.system() or "unknown", __version__
    )


def benchmark_run_metadata(seed: int, repeats: int) -> dict[str, object]:
    """Describe reproducibility inputs without treating timings as portable."""
    if seed < 0 or repeats <= 0:
        raise ValueError("benchmark metadata inputs are invalid")
    environment = asdict(benchmark_environment())
    return {
        "schema_version": "1.0",
        "seed": seed,
        "repeats": repeats,
        "environment": environment,
        "machine_dependent": True,
    }


@dataclass(frozen=True, slots=True)
class ThroughputSummary:
    case: str
    work_items: int
    items_per_second: float


def benchmark_throughput(summary: BenchmarkSummary, work_items: int) -> ThroughputSummary:
    """Convert measured mean latency to item throughput."""
    if work_items <= 0 or summary.mean_ms <= 0:
        raise ValueError("throughput requires positive work and elapsed time")
    return ThroughputSummary(
        summary.case, work_items, round(work_items / (summary.mean_ms / 1000), 6)
    )


@dataclass(frozen=True, slots=True)
class BenchmarkBaseline:
    case: str
    mean_ms: float
    tolerance_ratio: float = 10.0

    def __post_init__(self) -> None:
        if not self.case or self.mean_ms <= 0 or self.tolerance_ratio < 1:
            raise ValueError("benchmark baseline fields are invalid")


@dataclass(frozen=True, slots=True)
class BaselineComparison:
    case: str
    ratio: float
    within_tolerance: bool


def compare_benchmark_baseline(
    summary: BenchmarkSummary, baseline: BenchmarkBaseline
) -> BaselineComparison:
    """Compare means by ratio so only order-of-magnitude drift fails."""
    if summary.case != baseline.case:
        raise ValueError("benchmark baseline case does not match summary")
    ratio = summary.mean_ms / baseline.mean_ms
    return BaselineComparison(summary.case, round(ratio, 6), ratio <= baseline.tolerance_ratio)


def benchmark_result_record(
    samples: tuple[BenchmarkSample, ...], *, seed: int, repeats: int
) -> dict[str, object]:
    """Assemble metadata and computed summaries for a benchmark suite."""
    summaries = benchmark_summaries(samples)
    return {
        "metadata": benchmark_run_metadata(seed, repeats),
        "summaries": [asdict(summary) for summary in summaries],
        "samples": len(samples),
    }


def encode_benchmark_summaries(summaries: tuple[BenchmarkSummary, ...]) -> bytes:
    """Encode checksummed summary artifacts distinct from raw samples."""
    return encode_jsonl(
        ArtifactEnvelope.create("benchmark-summary", asdict(summary), "1.0")
        for summary in summaries
    )


def decode_benchmark_summaries(data: bytes) -> tuple[BenchmarkSummary, ...]:
    envelopes = decode_jsonl(data)
    if any(item.kind != "benchmark-summary" or item.schema_version != "1.0" for item in envelopes):
        raise ValueError("benchmark summary JSONL contains an unsupported artifact")
    return tuple(BenchmarkSummary(**item.payload) for item in envelopes)


def select_benchmark_case(
    samples: tuple[BenchmarkSample, ...], case: str
) -> tuple[BenchmarkSample, ...]:
    """Select one nonempty case from a combined benchmark run."""
    selected = tuple(sample for sample in samples if sample.case == case)
    if not selected:
        raise KeyError(f"benchmark case not found: {case}")
    return selected
