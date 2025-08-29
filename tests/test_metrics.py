import pytest

from echoparley.metrics import (
    BoundaryScores,
    accuracy,
    error_rate,
    evaluation_table,
    match_boundaries,
)


def test_boundary_matching_known_values() -> None:
    assert match_boundaries((100, 500), (90, 300, 510), 20) == BoundaryScores(1.0, 0.666667, 0.8, 2)
    assert match_boundaries((), ()) == BoundaryScores(1.0, 1.0, 1.0, 0)


def test_rates_stay_bounded() -> None:
    assert error_rate(1, 4) == 0.25
    assert accuracy(3, 4) == 0.75
    with pytest.raises(ValueError):
        error_rate(2, 1)


def test_evaluation_table_labels_planted_data() -> None:
    table = evaluation_table(BoundaryScores(1, 1, 1, 2), 0.1, 0.2, 0.9)
    assert table["data_origin"] == "synthetic-planted"
    assert all(
        0 <= table[key] <= 1
        for key in (
            "boundary_f1",
            "false_interrupt_rate",
            "missed_barge_in_rate",
            "floor_hold_accuracy",
        )
    )


def test_chance_corrected_agreement_matches_hand_computation() -> None:
    from echoparley.metrics import chance_corrected_agreement

    assert chance_corrected_agreement((True, True, False, False), (True, False, True, False)) == 0.0
    assert chance_corrected_agreement((True, False, True), (True, False, True)) == 1.0


def test_chance_agreement_handles_constant_and_invalid_vectors() -> None:
    import pytest

    from echoparley.metrics import chance_corrected_agreement

    assert chance_corrected_agreement((False, False), (False, False)) == 1.0
    with pytest.raises(ValueError, match="equal nonzero"):
        chance_corrected_agreement((True,), ())


def test_transition_entropy_has_known_uniform_value() -> None:
    from echoparley.metrics import transition_entropy

    assert transition_entropy(("a", "b", "a", "a", "b")) == 1.5
    assert transition_entropy(("a",)) == 0.0
