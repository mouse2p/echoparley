import numpy as np
import pytest

from echoparley.vq import CodebookHealth, codebook_health


def test_codebook_health_matches_balanced_usage() -> None:
    health = codebook_health(np.array([0, 0, 1, 1]), 4)
    assert health == CodebookHealth(4, 2, 0.5, 2.0, 0.5)


def test_codebook_health_handles_empty_and_invalid_assignments() -> None:
    assert codebook_health(np.array([], dtype=np.int64), 3).perplexity == 1.0
    with pytest.raises(ValueError, match="inside"):
        codebook_health(np.array([3]), 3)
    with pytest.raises(ValueError, match="inside"):
        codebook_health(np.ones((2, 1), dtype=np.int64), 3)


def test_collapse_assessment_reports_triggering_thresholds() -> None:
    from echoparley.vq import assess_collapse

    collapsed = assess_collapse(codebook_health(np.zeros(8, dtype=np.int64), 8))
    assert collapsed.collapsed and collapsed.occupancy_below_threshold
    healthy = assess_collapse(codebook_health(np.arange(8), 8))
    assert not healthy.collapsed


def test_collapse_assessment_rejects_invalid_thresholds() -> None:
    from echoparley.vq import assess_collapse

    health = codebook_health(np.array([0]), 1)
    with pytest.raises(ValueError, match="thresholds"):
        assess_collapse(health, minimum_occupancy=1.1)
    with pytest.raises(ValueError, match="thresholds"):
        assess_collapse(health, minimum_perplexity=0.5)


def test_ema_codebook_initializes_independent_statistics() -> None:
    from echoparley.vq import initialize_ema_codebook

    source = np.array([[0.0, 1.0], [2.0, 3.0]])
    state = initialize_ema_codebook(source)
    source[0, 0] = 99
    assert state.centroids[0, 0] == 0 and state.counts.tolist() == [1, 1]


def test_ema_step_moves_centroids_toward_assigned_embeddings() -> None:
    from echoparley.vq import ema_codebook_step, initialize_ema_codebook

    state = initialize_ema_codebook(np.array([[0.0], [10.0]]))
    updated = ema_codebook_step(
        state, np.array([[2.0], [4.0], [8.0]]), np.array([0, 0, 1]), decay=0.5
    )
    assert 0 < updated.centroids[0, 0] < 3
    assert 8 < updated.centroids[1, 0] < 10


def test_ema_step_does_not_drift_unused_codes() -> None:
    from echoparley.vq import ema_codebook_step, initialize_ema_codebook

    state = initialize_ema_codebook(np.array([[0.0], [10.0]]))
    updated = ema_codebook_step(state, np.array([[2.0]]), np.array([0]), decay=0.5)
    assert updated.centroids[1, 0] == 10


def test_ema_step_rejects_bad_decay_and_assignments() -> None:
    from echoparley.vq import ema_codebook_step, initialize_ema_codebook

    state = initialize_ema_codebook(np.zeros((2, 1)))
    with pytest.raises(ValueError, match="decay"):
        ema_codebook_step(state, np.ones((1, 1)), np.array([0]), decay=1)
    with pytest.raises(ValueError, match="outside"):
        ema_codebook_step(state, np.ones((1, 1)), np.array([2]))


def test_dead_code_indices_use_strict_count_threshold() -> None:
    from echoparley.vq import dead_code_indices

    assert dead_code_indices(np.array([0.0, 0.5, 2.0]), minimum_count=0.5) == (0,)


def test_dead_code_revival_is_seeded_and_updates_statistics() -> None:
    from echoparley.vq import EMACodebook, revive_dead_codes

    state = EMACodebook(np.zeros((2, 1)), np.array([0.0, 2.0]), np.zeros((2, 1)))
    values = np.array([[3.0], [4.0]])
    first = revive_dead_codes(state, values, seed=7)
    second = revive_dead_codes(state, values, seed=7)
    np.testing.assert_array_equal(first.centroids, second.centroids)
    assert first.counts[0] == 1 and first.centroids[0, 0] in {3, 4}


def test_revival_returns_healthy_state_unchanged() -> None:
    from echoparley.vq import initialize_ema_codebook, revive_dead_codes

    state = initialize_ema_codebook(np.array([[1.0], [2.0]]))
    assert revive_dead_codes(state, np.array([[9.0]])) is state


def test_vq_loss_curve_validates_parallel_series() -> None:
    from echoparley.vq import VQLossCurve

    assert VQLossCurve((1.0, 0.5), (0.2, 0.1)).steps == 2
    with pytest.raises(ValueError, match="equal"):
        VQLossCurve((1.0,), ())
