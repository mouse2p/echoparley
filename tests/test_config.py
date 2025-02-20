"""Validation tests for reproducible experiment configuration."""

from __future__ import annotations

import math

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


@pytest.mark.parametrize("field", ["seed", "sample_rate", "frame_ms", "hop_ms"])
def test_config_rejects_booleans(field: str) -> None:
    with pytest.raises(TypeError, match="boolean"):
        ExperimentConfig(**{field: True})


def test_config_mapping_roundtrip_is_canonical() -> None:
    config = ExperimentConfig(seed=17, sample_rate=24_000, frame_ms=25.0, hop_ms=12.5)
    assert config.to_mapping() == {
        "frame_ms": 25.0,
        "hop_ms": 12.5,
        "sample_rate": 24_000,
        "seed": 17,
    }
    assert ExperimentConfig.from_mapping(config.to_mapping()) == config
    assert config.fingerprint() == "7807ec4da4d6906c"


def test_config_mapping_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="unknown config keys: extra"):
        ExperimentConfig.from_mapping({"extra": 1})


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_config_rejects_nonfinite_frame_values(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        ExperimentConfig(frame_ms=value)
