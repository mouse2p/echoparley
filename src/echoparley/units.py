"""Deterministic NumPy semantic-unit extraction for synthetic features."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class PCAProjection:
    """Mean-centered orthonormal projection fitted with deterministic SVD."""

    mean: FloatArray
    components: FloatArray

    def transform(self, values: FloatArray) -> FloatArray:
        matrix = np.asarray(values, dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[1] != len(self.mean):
            raise ValueError("PCA input feature width does not match projection")
        return (matrix - self.mean) @ self.components.T

    def inverse_transform(self, values: FloatArray) -> FloatArray:
        matrix = np.asarray(values, dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[1] != len(self.components):
            raise ValueError("PCA latent width does not match projection")
        return matrix @ self.components + self.mean


def fit_pca(values: FloatArray, dimensions: int) -> PCAProjection:
    """Fit a projection while fixing component signs for stable serialization."""
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2 or len(matrix) < 2:
        raise ValueError("PCA requires a matrix with at least two rows")
    if not 1 <= dimensions <= min(matrix.shape):
        raise ValueError("PCA dimensions exceed matrix rank bounds")
    mean = matrix.mean(axis=0)
    _, _, components = np.linalg.svd(matrix - mean, full_matrices=False)
    selected = components[:dimensions].copy()
    pivots = np.argmax(np.abs(selected), axis=1)
    signs = np.where(selected[np.arange(dimensions), pivots] < 0, -1.0, 1.0)
    selected *= signs[:, None]
    return PCAProjection(mean, selected)


def retained_variance(values: FloatArray, projection: PCAProjection) -> float:
    """Return the finite-sample variance fraction represented by a projection."""
    matrix = np.asarray(values, dtype=np.float64)
    centered = matrix - matrix.mean(axis=0)
    total = float(np.sum(centered**2))
    if total == 0.0:
        return 1.0
    reconstructed = projection.inverse_transform(projection.transform(matrix))
    residual = float(np.sum((matrix - reconstructed) ** 2))
    return round(max(0.0, min(1.0, 1.0 - residual / total)), 12)


@dataclass(frozen=True, slots=True)
class KMeansCodebook:
    """Centroids ordered by their seeded initialization slots."""

    centroids: FloatArray

    def assign(self, values: FloatArray) -> IntArray:
        matrix = np.asarray(values, dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[1] != self.centroids.shape[1]:
            raise ValueError("feature width does not match codebook")
        distances = np.sum((matrix[:, None, :] - self.centroids[None, :, :]) ** 2, axis=2)
        assignments: IntArray = np.argmin(distances, axis=1).astype(np.int64)
        return assignments


def fit_kmeans(
    values: FloatArray, clusters: int, *, seed: int = 0, iterations: int = 50
) -> KMeansCodebook:
    """Fit Lloyd k-means from distinct seeded observations."""
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2 or not np.all(np.isfinite(matrix)):
        raise ValueError("k-means values must be a finite matrix")
    if not 1 <= clusters <= len(matrix) or iterations <= 0:
        raise ValueError("invalid cluster count or iteration limit")
    rng = np.random.default_rng(seed)
    centroids = matrix[rng.choice(len(matrix), clusters, replace=False)].copy()
    for _ in range(iterations):
        assignments = KMeansCodebook(centroids).assign(matrix)
        updated = centroids.copy()
        for index in range(clusters):
            members = matrix[assignments == index]
            if len(members):
                updated[index] = members.mean(axis=0)
        if np.array_equal(updated, centroids):
            break
        centroids = updated
    return KMeansCodebook(centroids)


@dataclass(frozen=True, slots=True)
class UnitExtractor:
    """Composed PCA projection and semantic codebook."""

    projection: PCAProjection
    codebook: KMeansCodebook

    def extract(self, features: FloatArray) -> IntArray:
        return self.codebook.assign(self.projection.transform(features))


def fit_unit_extractor(
    features: FloatArray, dimensions: int, clusters: int, *, seed: int = 0
) -> UnitExtractor:
    """Fit both deterministic stages on the same synthetic feature matrix."""
    projection = fit_pca(features, dimensions)
    codebook = fit_kmeans(projection.transform(features), clusters, seed=seed)
    return UnitExtractor(projection, codebook)


def collapse_units(identifiers: IntArray) -> tuple[IntArray, IntArray]:
    """Run-length encode unit IDs into IDs and positive frame durations."""
    values = np.asarray(identifiers, dtype=np.int64)
    if values.ndim != 1 or np.any(values < 0):
        raise ValueError("unit identifiers must be a non-negative vector")
    if len(values) == 0:
        return values.copy(), values.copy()
    boundaries = np.flatnonzero(np.concatenate(([True], values[1:] != values[:-1], [True])))
    return values[boundaries[:-1]], np.diff(boundaries).astype(np.int64)


def expand_units(identifiers: IntArray, durations: IntArray) -> IntArray:
    """Expand run-length encoded units to one ID per frame."""
    ids = np.asarray(identifiers, dtype=np.int64)
    counts = np.asarray(durations, dtype=np.int64)
    if ids.ndim != 1 or counts.ndim != 1 or len(ids) != len(counts) or np.any(counts <= 0):
        raise ValueError("unit IDs and positive durations must have equal vector lengths")
    if np.any(ids < 0):
        raise ValueError("unit identifiers must be non-negative")
    return np.repeat(ids, counts).astype(np.int64)


@dataclass(frozen=True, slots=True)
class UnitSpan:
    """A semantic unit aligned to a half-open frame interval."""

    identifier: int
    start_frame: int
    end_frame: int


def align_unit_runs(identifiers: IntArray, durations: IntArray) -> tuple[UnitSpan, ...]:
    """Map collapsed units to contiguous frame spans."""
    expanded = expand_units(identifiers, durations)
    ids, counts = collapse_units(expanded)
    starts = np.concatenate(([0], np.cumsum(counts)[:-1]))
    return tuple(
        UnitSpan(int(identifier), int(start), int(start + count))
        for identifier, start, count in zip(ids, starts, counts, strict=True)
    )


@dataclass(frozen=True, slots=True)
class CodebookUsage:
    """Observed occupancy and entropy perplexity for a fixed codebook."""

    occupied: int
    total: int
    perplexity: float


def codebook_usage(identifiers: IntArray, codebook_size: int) -> CodebookUsage:
    """Measure unit usage without claiming semantic quality."""
    values = np.asarray(identifiers, dtype=np.int64)
    if codebook_size <= 0 or values.ndim != 1 or np.any((values < 0) | (values >= codebook_size)):
        raise ValueError("unit identifiers fall outside the codebook")
    counts = np.bincount(values, minlength=codebook_size)
    probabilities = counts[counts > 0] / max(1, len(values))
    entropy = -float(np.sum(probabilities * np.log(probabilities))) if len(values) else 0.0
    return CodebookUsage(
        int(np.count_nonzero(counts)), codebook_size, round(float(np.exp(entropy)), 6)
    )


def fit_prosody_unit_extractor(
    acoustic_features: FloatArray,
    prosodic_features: FloatArray,
    dimensions: int,
    clusters: int,
    *,
    prosody_weight: float = 1.0,
    seed: int = 0,
) -> UnitExtractor:
    """Fit units over acoustic columns augmented by measured prosodic columns."""
    acoustic = np.asarray(acoustic_features, dtype=np.float64)
    prosody = np.asarray(prosodic_features, dtype=np.float64)
    if acoustic.ndim != 2 or prosody.ndim != 2 or len(acoustic) != len(prosody):
        raise ValueError("acoustic and prosodic feature rows must align")
    if prosody_weight < 0 or not np.all(np.isfinite(prosody)):
        raise ValueError("prosody weight and values must be finite and non-negative")
    combined = np.concatenate((acoustic, prosody * prosody_weight), axis=1)
    return fit_unit_extractor(combined, dimensions, clusters, seed=seed)
