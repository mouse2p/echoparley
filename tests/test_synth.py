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


def test_booking_scenario_is_reproducible_and_sorted() -> None:
    first = synth.booking_scenario(4)
    assert first == synth.booking_scenario(4)
    assert first.name == "booking" and first.duration_ms == 2_450
    assert [turn.kind for turn in first.turns].count("hold") == 1
    assert first.overlaps() == ()


def test_overlap_templates_have_planted_event_kinds() -> None:
    barge = synth.barge_in_scenario(3)
    backchannels = synth.backchannel_scenario(2)
    question = synth.question_scenario(1)
    assert len(barge.overlaps()) == 1
    assert [turn.kind for turn in barge.turns].count("interrupt") == 1
    assert len(backchannels.overlaps()) == 2
    assert [turn.kind for turn in backchannels.turns].count("backchannel") == 2
    assert {turn.topic for turn in question.turns} == {"weather"}


def test_rendered_dialogue_channels_are_seeded() -> None:
    scenario = synth.make_scenario("barge-in", 7)
    profiles = {
        "a": synth.SpeakerProfile("a", 110.0, (500.0,)),
        "b": synth.SpeakerProfile("b", 180.0, (700.0,)),
    }
    first = synth.render_dialogue(scenario, profiles, 2_000)
    second = synth.render_dialogue(scenario, profiles, 2_000)
    assert set(first) == {"a", "b"}
    np.testing.assert_array_equal(first["a"].samples, second["a"].samples)
    assert np.count_nonzero(first["a"].samples * first["b"].samples) > 0


def test_renderer_requires_every_speaker_profile() -> None:
    with pytest.raises(ValueError, match="missing speaker profiles: b"):
        synth.render_dialogue(
            synth.barge_in_scenario(), {"a": synth.SpeakerProfile("a", 100, (500,))}
        )


def test_dialogue_accepts_three_speakers() -> None:
    turns = tuple(
        synth.TurnAnnotation(speaker, index * 10, index * 10 + 8, speaker)
        for index, speaker in enumerate(("a", "b", "c"))
    )
    assert {turn.speaker for turn in synth.DialogueScenario("trio", 0, turns).turns} == {
        "a",
        "b",
        "c",
    }


def test_dialogue_rejects_a_fourth_speaker() -> None:
    turns = tuple(
        synth.TurnAnnotation(speaker, index * 10, index * 10 + 8, speaker)
        for index, speaker in enumerate(("a", "b", "c", "d"))
    )
    with pytest.raises(ValueError, match="three speakers"):
        synth.DialogueScenario("crowd", 0, turns)
