import numpy as np

from echoparley.prosody import autocorrelation_f0


def test_autocorrelation_pitch_tracks_a_synthetic_tone() -> None:
    sample_rate = 8_000
    time = np.arange(4_000) / sample_rate
    track = autocorrelation_f0(np.sin(2 * np.pi * 200 * time), sample_rate)
    assert len(track.frequencies_hz) == 24
    assert np.median(track.frequencies_hz) == 200.0
    assert np.all(track.strengths > 0.5)


def test_pitch_marks_silence_unvoiced_and_short_inputs_empty() -> None:
    silent = autocorrelation_f0(np.zeros(640), 8_000)
    assert silent.frequencies_hz.tolist() == [0.0, 0.0, 0.0]
    assert silent.strengths.tolist() == [0.0, 0.0, 0.0]
    short = autocorrelation_f0(np.zeros(319), 8_000)
    assert short.times_seconds.size == short.frequencies_hz.size == 0


def test_moving_average_smooths_voiced_values_without_bridging_silence() -> None:
    from echoparley.prosody import moving_average_contour

    values = np.array([100.0, 130.0, 0.0, 110.0, 120.0])
    assert moving_average_contour(values).tolist() == [115.0, 115.0, 0.0, 115.0, 115.0]


def test_pitch_rejects_invalid_search_and_smoothing_parameters() -> None:
    import pytest

    from echoparley.prosody import moving_average_contour

    with pytest.raises(ValueError, match="range"):
        autocorrelation_f0(np.ones(400), 8_000, min_hz=400, max_hz=200)
    with pytest.raises(ValueError, match="odd"):
        moving_average_contour(np.ones(4), 2)
