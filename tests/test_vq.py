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
