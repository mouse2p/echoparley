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


def test_mock_punctuation_preserves_empty_input_and_validates_marks() -> None:
    import pytest

    from echoparley.cascade import MockPunctuation

    assert MockPunctuation()("   ") == ""
    with pytest.raises(ValueError, match="unsupported"):
        MockPunctuation(",")


def test_mock_tts_alignment_covers_each_scripted_word() -> None:
    from echoparley.cascade import MockTTSAlignment

    aligned = MockTTSAlignment(50)("hello world")
    assert [(item.start_ms, item.end_ms, item.text) for item in aligned] == [
        (0, 50, "hello"),
        (50, 100, "world"),
    ]
    assert all(0 <= item.identifier < 64 for item in aligned)


def test_mock_tts_alignment_handles_empty_text_and_bad_duration() -> None:
    import pytest

    from echoparley.cascade import MockTTSAlignment

    assert MockTTSAlignment()("") == ()
    with pytest.raises(ValueError, match="positive"):
        MockTTSAlignment(0)


def test_stage_latency_ledger_is_immutable_and_exact() -> None:
    from echoparley.cascade import StageLatencyLedger

    first = StageLatencyLedger().append("vad", 10)
    second = first.append("stt", 20)
    assert first.total_ms == 10 and second.total_ms == 30
    assert [item.name for item in second.timings] == ["vad", "stt"]


def test_stage_timing_rejects_blank_names_and_negative_delay() -> None:
    import pytest

    from echoparley.cascade import StageTiming

    with pytest.raises(ValueError, match="name"):
        StageTiming("", 1)
    with pytest.raises(ValueError, match="non-negative"):
        StageTiming("stt", -1)
