import numpy as np

from echoparley.prosody import autocorrelation_f0


def test_autocorrelation_pitch_tracks_a_synthetic_tone() -> None:
    sample_rate = 8_000
    time = np.arange(4_000) / sample_rate
    track = autocorrelation_f0(np.sin(2 * np.pi * 200 * time), sample_rate)
    assert len(track.frequencies_hz) == 24
    assert np.median(track.frequencies_hz) == 200.0
    assert np.all(track.strengths > 0.5)
