"""Deterministic unit fitting, alignment, and usage tests."""

from __future__ import annotations

import numpy as np
import pytest

from echoparley import units


def test_full_rank_pca_roundtrip_and_sign_stability() -> None:
    values = np.array([[1.0, 2.0], [2.0, 0.0], [4.0, 3.0]])
    projection = units.fit_pca(values, 2)
    latent = projection.transform(values)
    np.testing.assert_allclose(projection.inverse_transform(latent), values, atol=1e-12)
    pivots = np.argmax(np.abs(projection.components), axis=1)
    assert np.all(projection.components[np.arange(2), pivots] >= 0)


@pytest.mark.parametrize("dimensions", [0, 3])
def test_pca_rejects_invalid_dimension_count(dimensions: int) -> None:
    with pytest.raises(ValueError, match="dimensions"):
        units.fit_pca(np.ones((3, 2)), dimensions)


def test_retained_variance_has_known_limits() -> None:
    values = np.array([[0.0, 0.0], [1.0, 2.0], [2.0, 4.0]])
    assert units.retained_variance(values, units.fit_pca(values, 1)) == 1.0
    constant = np.ones((3, 2))
    assert units.retained_variance(constant, units.fit_pca(constant, 1)) == 1.0


def test_kmeans_is_seeded_and_finds_separated_groups() -> None:
    values = np.array([[-2.1], [-2.0], [-1.9], [1.9], [2.0], [2.1]])
    first = units.fit_kmeans(values, 2, seed=4)
    second = units.fit_kmeans(values, 2, seed=4)
    np.testing.assert_array_equal(first.centroids, second.centroids)
    assert sorted(first.centroids[:, 0].tolist()) == [-2.0, 2.0]
    labels = first.assign(np.array([[-2.0], [2.0]]))
    assert labels[0] != labels[1]


def test_kmeans_rejects_more_clusters_than_rows() -> None:
    with pytest.raises(ValueError, match="cluster count"):
        units.fit_kmeans(np.ones((2, 1)), 3)
