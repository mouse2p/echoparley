import numpy as np

from echoparley.cascade import MockVAD, VoiceActivitySpan


def test_mock_vad_extracts_half_open_speech_spans() -> None:
    energy = np.array([0.0, 0.1, 0.2, 0.0, 0.05, 0.0])
    assert MockVAD(0.05)(energy) == (VoiceActivitySpan(1, 3), VoiceActivitySpan(4, 5))


def test_mock_vad_validates_thresholds_and_finite_energy() -> None:
    import pytest

    with pytest.raises(ValueError, match="threshold"):
        MockVAD(-0.1)
    with pytest.raises(ValueError, match="finite"):
        MockVAD()(np.array([np.nan]))
    assert MockVAD()(np.array([])) == ()


def test_mock_punctuation_normalizes_spacing_and_terminal_mark() -> None:
    from echoparley.cascade import MockPunctuation

    assert MockPunctuation()("  hello   synthetic world ") == "Hello synthetic world."
    assert MockPunctuation("?")("where now!") == "Where now!"
