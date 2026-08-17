"""Spectral feature boundaries and deterministic golden values."""

from __future__ import annotations

import numpy as np
import pytest

from echoparley import features


def test_periodic_windows_have_expected_values() -> None:
    np.testing.assert_allclose(features.analysis_window(4), [0.0, 0.5, 1.0, 0.5])
    np.testing.assert_allclose(features.analysis_window(4, "hamming"), [0.08, 0.54, 1.0, 0.54])
    assert features.analysis_window(3, "rectangular").tolist() == [1.0, 1.0, 1.0]


@pytest.mark.parametrize("length,kind", [(0, "hann"), (4, "triangle")])
def test_analysis_window_rejects_invalid_requests(length: int, kind: str) -> None:
    with pytest.raises(ValueError):
        features.analysis_window(length, kind)


def test_power_spectrum_shape_and_rectangular_impulse() -> None:
    frames = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]])
    spectrum = features.power_spectrum(frames, window="rectangular")
    assert spectrum.dtype == np.float64
    assert spectrum.shape == (2, 3)
    np.testing.assert_allclose(spectrum[0], [0.25, 0.25, 0.25])
    np.testing.assert_array_equal(spectrum[1], np.zeros(3))


def test_power_spectrum_rejects_vectors_and_empty_width() -> None:
    with pytest.raises(ValueError, match="matrix"):
        features.power_spectrum(np.ones(4))
    with pytest.raises(ValueError, match="nonempty-width"):
        features.power_spectrum(np.empty((2, 0)))


def test_hertz_mel_roundtrip() -> None:
    frequencies = np.array([0.0, 80.0, 440.0, 8_000.0])
    np.testing.assert_allclose(
        features.mel_to_hertz(features.hertz_to_mel(frequencies)), frequencies
    )


@pytest.mark.parametrize("function", [features.hertz_to_mel, features.mel_to_hertz])
def test_frequency_transforms_reject_negative_values(function: object) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        function(-1.0)  # type: ignore[operator]


def test_mel_filterbank_is_nonnegative_and_normalized() -> None:
    filters = features.mel_filterbank(16_000, 512, 24)
    assert filters.shape == (24, 257)
    assert np.all(filters >= 0)
    np.testing.assert_allclose(filters.sum(axis=1), np.ones(24))
    assert np.all(np.argmax(filters, axis=1)[:-1] < np.argmax(filters, axis=1)[1:])


def test_mel_filterbank_rejects_excess_resolution() -> None:
    with pytest.raises(ValueError, match="too many"):
        features.mel_filterbank(16_000, 8, 5)


def test_log_mel_silence_uses_exact_floor() -> None:
    result = features.log_mel_features(np.zeros((2, 64)), 8_000, 8, floor=1e-6)
    np.testing.assert_allclose(result, np.full((2, 8), np.log(1e-6)))


@pytest.mark.parametrize("floor", [0.0, -1.0, np.inf])
def test_log_mel_rejects_invalid_floors(floor: float) -> None:
    with pytest.raises(ValueError, match="floor"):
        features.log_mel_features(np.zeros((1, 16)), 8_000, 2, floor=floor)


def test_sliding_statistics_clip_context_at_edges() -> None:
    values = np.array([[1.0], [3.0], [8.0]])
    result = features.sliding_statistics(values, 1)
    np.testing.assert_allclose(result[:, 0], [2.0, 4.0, 5.5])
    np.testing.assert_allclose(result[:, 1], [1.0, np.std([1, 3, 8]), 2.5])


def test_zero_radius_statistics_have_zero_variance() -> None:
    values = np.array([[2.0, 4.0]])
    assert features.sliding_statistics(values, 0).tolist() == [[2.0, 4.0, 0.0, 0.0]]


def test_temporal_deltas_preserve_shape_and_direction() -> None:
    values = np.array([[0.0], [2.0], [6.0]])
    assert features.temporal_deltas(values).tolist() == [[1.0], [3.0], [2.0]]
    assert features.temporal_deltas(np.empty((0, 2))).shape == (0, 2)


@pytest.mark.parametrize("kind", ["hann", "hamming", "rectangular"])
def test_single_sample_window_has_unit_gain(kind: str) -> None:
    assert features.analysis_window(1, kind).tolist() == [1.0]
