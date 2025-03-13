"""Audio transport, framing, and alignment tests."""

from __future__ import annotations

import numpy as np
import pytest

from echoparley import audio


def test_audio_buffer_copies_and_freezes_samples() -> None:
    source = np.array([0.0, 0.5, -0.5])
    buffer = audio.AudioBuffer(source, 2)
    source[1] = 0.0
    assert buffer.samples.tolist() == [0.0, 0.5, -0.5]
    assert buffer.duration_seconds == 1.5
    assert not buffer.samples.flags.writeable


@pytest.mark.parametrize(
    "samples,rate,message",
    [
        (np.zeros((2, 2)), 16_000, "one-dimensional"),
        (np.array([1.01]), 16_000, "normalized"),
        (np.array([np.nan]), 16_000, "finite"),
        (np.zeros(1), 0, "positive"),
    ],
)
def test_audio_buffer_rejects_invalid_inputs(samples: np.ndarray, rate: int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        audio.AudioBuffer(samples, rate)


def test_pcm16_roundtrip_including_endpoints() -> None:
    samples = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    encoded = audio.encode_pcm16(samples)
    assert encoded.hex() == "008000c000000040ff7f"
    np.testing.assert_allclose(audio.decode_pcm16(encoded), samples, atol=1 / 32767)


def test_pcm16_rejects_odd_byte_count() -> None:
    with pytest.raises(ValueError, match="length must be even"):
        audio.decode_pcm16(b"\x00")
