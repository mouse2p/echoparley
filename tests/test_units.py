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


def test_unit_extractor_returns_one_id_per_frame() -> None:
    features = np.array([[-2.0, 0.0], [-1.8, 0.1], [2.0, 0.0], [1.8, -0.1]])
    extractor = units.fit_unit_extractor(features, 2, 2, seed=8)
    identifiers = extractor.extract(features)
    assert identifiers.shape == (4,)
    assert set(identifiers.tolist()) == {0, 1}
    np.testing.assert_array_equal(identifiers, extractor.extract(features.copy()))


def test_unit_run_length_roundtrip() -> None:
    original = np.array([3, 3, 3, 1, 1, 4], dtype=np.int64)
    identifiers, durations = units.collapse_units(original)
    assert identifiers.tolist() == [3, 1, 4]
    assert durations.tolist() == [3, 2, 1]
    np.testing.assert_array_equal(units.expand_units(identifiers, durations), original)


def test_empty_unit_run_roundtrip() -> None:
    identifiers, durations = units.collapse_units(np.array([], dtype=np.int64))
    assert units.expand_units(identifiers, durations).size == 0


def test_unit_alignment_covers_frames_without_gaps() -> None:
    spans = units.align_unit_runs(np.array([2, 5]), np.array([3, 2]))
    assert spans == (units.UnitSpan(2, 0, 3), units.UnitSpan(5, 3, 5))
    assert spans[0].end_frame == spans[1].start_frame


def test_codebook_usage_known_distributions() -> None:
    balanced = units.codebook_usage(np.array([0, 0, 1, 1]), 4)
    assert balanced == units.CodebookUsage(occupied=2, total=4, perplexity=2.0)
    empty = units.codebook_usage(np.array([], dtype=np.int64), 3)
    assert empty == units.CodebookUsage(occupied=0, total=3, perplexity=1.0)


def test_codebook_usage_rejects_out_of_range_ids() -> None:
    with pytest.raises(ValueError, match="outside"):
        units.codebook_usage(np.array([2]), 2)
