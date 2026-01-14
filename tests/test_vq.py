import numpy as np

from echoparley.vq import CodebookHealth, codebook_health


def test_codebook_health_matches_balanced_usage() -> None:
    health = codebook_health(np.array([0, 0, 1, 1]), 4)
    assert health == CodebookHealth(4, 2, 0.5, 2.0, 0.5)
