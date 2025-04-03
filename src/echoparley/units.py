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
