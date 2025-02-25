"""Golden and corruption tests for serialized artifacts."""

from __future__ import annotations

import math

import pytest

from echoparley.artifacts import canonical_json, content_checksum


def test_canonical_json_sorts_keys_and_preserves_unicode() -> None:
    value = {"z": [2, 1], "speaker": "甲", "a": {"enabled": True}}
    encoded = '{"a":{"enabled":true},"speaker":"甲","z":[2,1]}'
    assert canonical_json(value) == encoded
    assert (
        content_checksum(value)
        == "6df35e0afe44a3ca0639c6d9041cd7c0789eec0ac2cd555e3d85ebc8dd8709d9"
    )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_canonical_json_rejects_nonfinite_numbers(value: float) -> None:
    with pytest.raises(ValueError, match="JSON compliant"):
        canonical_json({"value": value})
