"""Reproducibility and planted-annotation tests for synthetic dialogues."""

from __future__ import annotations

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
