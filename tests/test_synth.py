"""Reproducibility and planted-annotation tests for synthetic dialogues."""

from __future__ import annotations

import numpy as np
import pytest

from echoparley import synth


def test_speaker_profile_records_signal_parameters() -> None:
    profile = synth.SpeakerProfile("speaker-a", 120.0, (500.0, 1_500.0))
    assert profile.amplitude == 0.25


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"name": ""}, "name"),
        ({"fundamental_hz": 0.0}, "frequencies"),
        ({"formants_hz": (-1.0,)}, "frequencies"),
        ({"amplitude": 1.1}, "amplitude"),
    ],
)
def test_speaker_profile_rejects_invalid_values(changes: dict[str, object], message: str) -> None:
    values = {"name": "a", "fundamental_hz": 120.0, "formants_hz": (500.0,)}
    values.update(changes)
    with pytest.raises(ValueError, match=message):
        synth.SpeakerProfile(**values)


def test_formant_synthesis_is_seeded_and_normalized() -> None:
    profile = synth.SpeakerProfile("a", 120.0, (500.0, 1_500.0))
    first = synth.synthesize_formants(profile, 0.05, 8_000, seed=9)
    second = synth.synthesize_formants(profile, 0.05, 8_000, seed=9)
    np.testing.assert_array_equal(first.samples, second.samples)
    assert len(first.samples) == 400
    assert np.max(np.abs(first.samples)) <= profile.amplitude
    assert not np.array_equal(
        first.samples, synth.synthesize_formants(profile, 0.05, 8_000, seed=10).samples
    )


def test_zero_duration_formant_signal_is_empty() -> None:
    profile = synth.SpeakerProfile("a", 120.0, (500.0,))
    assert synth.synthesize_formants(profile, 0.0, 8_000).samples.size == 0


def test_turn_annotation_accepts_overlap_semantics() -> None:
    annotation = synth.TurnAnnotation("b", 80, 120, "wait", "interrupt", "booking")
    assert annotation.end_ms - annotation.start_ms == 40
    assert annotation.kind in synth.TURN_KINDS


@pytest.mark.parametrize(
    "values", [("", 0, 1, "turn"), ("a", -1, 1, "turn"), ("a", 2, 2, "turn"), ("a", 0, 1, "noise")]
)
def test_turn_annotation_rejects_invalid_intervals(values: tuple[str, int, int, str]) -> None:
    with pytest.raises(ValueError):
        synth.TurnAnnotation(values[0], values[1], values[2], "text", values[3])
