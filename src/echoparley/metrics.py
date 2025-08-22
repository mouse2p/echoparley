"""Turn-taking metrics against explicitly planted synthetic annotations."""

from __future__ import annotations

from dataclasses import dataclass


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
