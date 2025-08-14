from __future__ import annotations

import pytest

from echoparley.torch_models import constrained_sample, torch_available


def test_constrained_decoding_never_selects_blocked_floor_token() -> None:
    assert constrained_sample([0.1, 9.0, 0.5], (0, 2)) == 2
    with pytest.raises(ValueError, match="constraints"):
        constrained_sample([1.0], ())


@pytest.mark.model
def test_vq_training_reduces_real_synthetic_loss() -> None:
    if not torch_available():
        pytest.skip("torch extra is not installed")
    from echoparley.torch_models import train_vq_demo

    summary = train_vq_demo(seed=4)
    assert summary.final_loss < summary.initial_loss
    assert summary.data_origin == "deterministic-synthetic"


@pytest.mark.model
def test_lm_training_reduces_real_synthetic_loss() -> None:
    if not torch_available():
        pytest.skip("torch extra is not installed")
    from echoparley.torch_models import train_lm_demo

    summary = train_lm_demo(seed=4)
    assert summary.final_loss < summary.initial_loss
