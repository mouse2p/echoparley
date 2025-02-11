"""Validation tests for reproducible experiment configuration."""

from __future__ import annotations

import pytest

from echoparley.config import ExperimentConfig


def test_default_config_uses_common_speech_framing() -> None:
    config = ExperimentConfig()
    assert (config.sample_rate, config.frame_samples, config.hop_samples) == (16_000, 320, 160)


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"seed": -1}, "seed"),
        ({"sample_rate": 7_999}, "sample_rate"),
        ({"sample_rate": 48_001}, "sample_rate"),
        ({"frame_ms": 0.0}, "positive"),
        ({"hop_ms": -0.1}, "positive"),
        ({"frame_ms": 10.0, "hop_ms": 10.1}, "cannot exceed"),
    ],
)
def test_config_rejects_invalid_boundaries(changes: dict[str, int | float], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        ExperimentConfig(**changes)
