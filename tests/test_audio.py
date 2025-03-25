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


def test_wav_roundtrip_preserves_rate_and_pcm_samples() -> None:
    original = audio.AudioBuffer(np.linspace(-1.0, 1.0, 17), 8_000)
    encoded = audio.write_wav(original)
    restored = audio.read_wav(encoded)
    assert encoded[:4] == b"RIFF" and encoded[8:12] == b"WAVE"
    assert restored.sample_rate == 8_000
    assert audio.encode_pcm16(restored.samples) == audio.encode_pcm16(original.samples)


@pytest.mark.parametrize("data", [b"", b"not a wave file"])
def test_wav_reader_reports_malformed_containers(data: bytes) -> None:
    with pytest.raises(ValueError, match="invalid WAV"):
        audio.read_wav(data)


def test_audio_framing_overlap_and_padding() -> None:
    samples = np.arange(7, dtype=np.float64)
    unpadded = audio.frame_audio(samples, 4, 2)
    padded = audio.frame_audio(samples, 4, 2, pad_end=True)
    assert unpadded.tolist() == [[0, 1, 2, 3], [2, 3, 4, 5]]
    assert padded.tolist() == [[0, 1, 2, 3], [2, 3, 4, 5], [4, 5, 6, 0]]


def test_audio_framing_short_input_policy() -> None:
    assert audio.frame_audio(np.array([1.0]), 3, 1).shape == (0, 3)
    assert audio.frame_audio(np.array([1.0]), 3, 1, pad_end=True).tolist() == [[1, 0, 0]]
    assert audio.frame_audio(np.array([]), 3, 1, pad_end=True).shape == (0, 3)


def test_frame_spans_match_padded_frame_coverage() -> None:
    spans = audio.frame_spans(7, 4, 2, pad_end=True)
    assert [(span.index, span.start_sample, span.end_sample) for span in spans] == [
        (0, 0, 4),
        (1, 2, 6),
        (2, 4, 7),
    ]


def test_frame_spans_reject_negative_sample_count() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        audio.frame_spans(-1, 4, 2)


def test_pcm_encoder_requires_explicit_clipping() -> None:
    values = np.array([-2.0, 2.0])
    with pytest.raises(ValueError, match="normalized range"):
        audio.encode_pcm16(values)
    assert audio.decode_pcm16(audio.encode_pcm16(values, clip=True)).tolist() == [-1.0, 1.0]
