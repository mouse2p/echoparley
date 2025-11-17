import numpy as np

from echoparley.cascade import MockVAD, VoiceActivitySpan


def test_mock_vad_extracts_half_open_speech_spans() -> None:
    energy = np.array([0.0, 0.1, 0.2, 0.0, 0.05, 0.0])
    assert MockVAD(0.05)(energy) == (VoiceActivitySpan(1, 3), VoiceActivitySpan(4, 5))
