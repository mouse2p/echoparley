"""Turn-taking metrics against explicitly planted synthetic annotations."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class BoundaryScores:
    precision: float
    recall: float
    f1: float
    matches: int


def match_boundaries(
    predicted: tuple[int, ...], planted: tuple[int, ...], tolerance_ms: int = 100
) -> BoundaryScores:
    """Greedily match each prediction to one planted boundary within tolerance."""
    if tolerance_ms < 0:
        raise ValueError("boundary tolerance must be non-negative")
    remaining = list(planted)
    matches = 0
    for value in sorted(predicted):
        candidates = [(abs(value - target), target) for target in remaining]
        if candidates:
            distance, target = min(candidates)
            if distance <= tolerance_ms:
                matches += 1
                remaining.remove(target)
    precision = matches / len(predicted) if predicted else float(not planted)
    recall = matches / len(planted) if planted else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return BoundaryScores(round(precision, 6), round(recall, 6), round(f1, 6), matches)


def error_rate(detected: int, opportunities: int) -> float:
    """Return a bounded false-interrupt or missed-barge-in rate."""
    if detected < 0 or opportunities < 0 or detected > opportunities:
        raise ValueError("metric counts require 0 <= detected <= opportunities")
    return round(detected / opportunities, 6) if opportunities else 0.0


def accuracy(correct: int, total: int) -> float:
    """Return bounded floor-hold accuracy with an empty-set identity."""
    if correct < 0 or total < 0 or correct > total:
        raise ValueError("accuracy counts require 0 <= correct <= total")
    return round(correct / total, 6) if total else 1.0


def evaluation_table(
    boundaries: BoundaryScores,
    false_interrupts: float,
    missed_barge_ins: float,
    floor_hold_accuracy: float,
) -> dict[str, float | int | str]:
    values = (false_interrupts, missed_barge_ins, floor_hold_accuracy)
    if any(not 0 <= value <= 1 for value in values):
        raise ValueError("evaluation metrics must be in [0, 1]")
    return {
        "data_origin": "synthetic-planted",
        "boundary_f1": boundaries.f1,
        "boundary_matches": boundaries.matches,
        "false_interrupt_rate": round(false_interrupts, 6),
        "missed_barge_in_rate": round(missed_barge_ins, 6),
        "floor_hold_accuracy": round(floor_hold_accuracy, 6),
    }


def chance_corrected_agreement(first: tuple[bool, ...], second: tuple[bool, ...]) -> float:
    """Compute Cohen-style kappa for two aligned boundary decision vectors."""
    if len(first) != len(second) or not first:
        raise ValueError("agreement vectors must have equal nonzero lengths")
    observed = sum(left == right for left, right in zip(first, second, strict=True)) / len(first)
    first_yes = sum(first) / len(first)
    second_yes = sum(second) / len(second)
    expected = first_yes * second_yes + (1 - first_yes) * (1 - second_yes)
    if expected == 1:
        return 1.0 if observed == 1 else 0.0
    return round((observed - expected) / (1 - expected), 6)


def transition_entropy(speakers: tuple[str, ...]) -> float:
    """Measure entropy of observed speaker-to-speaker transition pairs in bits."""
    if any(not speaker for speaker in speakers):
        raise ValueError("speaker labels cannot be empty")
    transitions = tuple(itertools.pairwise(speakers))
    if not transitions:
        return 0.0
    counts = {pair: transitions.count(pair) for pair in set(transitions)}
    probabilities = (count / len(transitions) for count in counts.values())
    return round(-sum(value * math.log2(value) for value in probabilities), 6)


@dataclass(frozen=True, slots=True)
class FloorControl:
    speaker_ms: dict[str, int]
    overlap_ms: int
    silence_ms: int

    @property
    def total_ms(self) -> int:
        return sum(self.speaker_ms.values()) + self.silence_ms - self.overlap_ms


@dataclass(frozen=True, slots=True)
class LatencyPercentiles:
    p50_ms: float
    p90_ms: float
    p99_ms: float


def latency_percentiles(values_ms: tuple[int, ...]) -> LatencyPercentiles:
    """Return linear-interpolated latency percentiles rounded at production."""
    if not values_ms or any(value < 0 for value in values_ms):
        raise ValueError("latencies must be a nonempty non-negative sample")
    values = np.asarray(values_ms, dtype=np.float64)
    results = np.percentile(values, (50, 90, 99))
    return LatencyPercentiles(*(round(float(value), 6) for value in results))


def floor_control_statistics(
    intervals: tuple[tuple[str, int, int], ...], duration_ms: int
) -> FloorControl:
    """Measure planted speaker occupancy, overlap, and silence on a millisecond grid."""
    if duration_ms < 0 or any(
        not speaker or start < 0 or end <= start or end > duration_ms
        for speaker, start, end in intervals
    ):
        raise ValueError("floor intervals must fit the dialogue duration")
    active = [set() for _ in range(duration_ms)]
    for speaker, start, end in intervals:
        for time_ms in range(start, end):
            active[time_ms].add(speaker)
    speakers = sorted({speaker for speaker, _, _ in intervals})
    occupancy = {speaker: sum(speaker in frame for frame in active) for speaker in speakers}
    return FloorControl(
        occupancy, sum(len(frame) > 1 for frame in active), sum(not frame for frame in active)
    )


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    estimate: float
    lower: float
    upper: float
    confidence: float


def bootstrap_mean_interval(
    values: tuple[float, ...], *, seed: int = 0, samples: int = 1_000, confidence: float = 0.95
) -> ConfidenceInterval:
    """Estimate a deterministic percentile bootstrap interval for a sample mean."""
    if not values or samples <= 0 or not 0 < confidence < 1 or not np.all(np.isfinite(values)):
        raise ValueError("bootstrap inputs are invalid")
    data = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(data, size=(samples, len(data)), replace=True), axis=1)
    tail = (1 - confidence) / 2
    lower, upper = np.quantile(means, (tail, 1 - tail))
    return ConfidenceInterval(
        round(float(np.mean(data)), 6), round(float(lower), 6), round(float(upper), 6), confidence
    )


@dataclass(frozen=True, slots=True)
class BoundaryConfusion:
    true_positive: int
    false_positive: int
    false_negative: int


def boundary_confusion(
    predicted: tuple[int, ...], planted: tuple[int, ...], tolerance_ms: int = 100
) -> BoundaryConfusion:
    """Return one-to-one greedy boundary match counts."""
    scores = match_boundaries(predicted, planted, tolerance_ms)
    return BoundaryConfusion(
        scores.matches, len(predicted) - scores.matches, len(planted) - scores.matches
    )
