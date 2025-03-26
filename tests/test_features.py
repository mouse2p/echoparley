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
    assert spectrum.shape == (2, 3)
    np.testing.assert_allclose(spectrum[0], [0.25, 0.25, 0.25])
    np.testing.assert_array_equal(spectrum[1], np.zeros(3))


def test_power_spectrum_rejects_vectors_and_empty_width() -> None:
    with pytest.raises(ValueError, match="matrix"):
        features.power_spectrum(np.ones(4))
    with pytest.raises(ValueError, match="nonempty-width"):
        features.power_spectrum(np.empty((2, 0)))
