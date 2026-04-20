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
    with pytest.raises(ValueError, match="finite"):
        autocorrelation_f0(np.array([np.nan] * 400), 8_000)


def test_tone_events_label_rises_and_falls() -> None:
    from echoparley.prosody import PitchTrack, annotate_tone_events

    track = PitchTrack(
        np.array([0.01, 0.02, 0.03, 0.04]),
        np.array([100.0, 130.0, 95.0, 0.0]),
        np.ones(4),
    )
    assert [(event.kind, event.change_hz) for event in annotate_tone_events(track)] == [
        ("rise", 30.0),
        ("fall", -35.0),
    ]


def test_median_contour_removes_an_isolated_pitch_spike() -> None:
    from echoparley.prosody import median_contour

    values = np.array([100.0, 102.0, 300.0, 101.0, 99.0])
    assert median_contour(values).tolist() == [101.0, 102.0, 102.0, 101.0, 100.0]


def test_prosodic_vector_measures_rate_pauses_and_declination() -> None:
    from echoparley.prosody import PitchTrack, ProsodicFeatures, prosodic_features

    track = PitchTrack(np.array([0.0, 1.0, 2.0]), np.array([140.0, 120.0, 100.0]), np.ones(3))
    assert prosodic_features(
        track, duration_seconds=4, word_count=8, pauses_seconds=(0.25, 0.75)
    ) == ProsodicFeatures(2.0, 0.5, 0.25, 40.0, -20.0)


def test_prosodic_vector_rejects_impossible_pause_timings() -> None:
    import pytest

    from echoparley.prosody import PitchTrack, prosodic_features

    empty = np.array([], dtype=np.float64)
    track = PitchTrack(empty, empty, empty)
    assert prosodic_features(track, duration_seconds=1, word_count=0).pitch_range_hz == 0
    with pytest.raises(ValueError, match="exceed"):
        prosodic_features(track, duration_seconds=1, word_count=0, pauses_seconds=(1.1,))


def test_prosody_array_has_a_stable_documented_order() -> None:
    from echoparley.prosody import ProsodicFeatures, prosody_array

    value = ProsodicFeatures(2.0, 0.3, 0.1, 40.0, -5.0)
    assert prosody_array(value).tolist() == [2.0, 0.3, 0.1, 40.0, -5.0]


def test_pitch_track_smoothing_preserves_timing_and_voicing_gaps() -> None:
    from echoparley.prosody import PitchTrack, smooth_pitch_track

    track = PitchTrack(np.arange(5.0), np.array([100.0, 300.0, 0.0, 100.0, 102.0]), np.ones(5))
    result = smooth_pitch_track(track)
    np.testing.assert_array_equal(result.times_seconds, track.times_seconds)
    assert result.frequencies_hz[2] == 0


def test_voiced_segments_use_half_open_frame_spans() -> None:
    from echoparley.prosody import PitchTrack, voiced_segments

    track = PitchTrack(np.arange(6.0), np.array([0, 100, 110, 0, 120, 0]), np.ones(6))
    assert voiced_segments(track) == ((1, 3), (4, 5))


def test_pitch_summary_ignores_unvoiced_frames() -> None:
    from echoparley.prosody import PitchSummary, PitchTrack, summarize_pitch

    track = PitchTrack(np.arange(4.0), np.array([0.0, 100.0, 120.0, 0.0]), np.ones(4))
    assert summarize_pitch(track) == PitchSummary(2, 0.5, 100.0, 110.0, 120.0)
