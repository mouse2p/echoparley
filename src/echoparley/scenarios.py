"""Expanded planted scenarios for the synthetic dialogue laboratory."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from echoparley.synth import DialogueScenario, TurnAnnotation


class BackchannelKind(StrEnum):
    """Planted listener-response functions, not inferred pragmatics."""

    ACKNOWLEDGE = "acknowledge"
    CONTINUER = "continuer"
    REPAIR = "repair"


_BACKCHANNEL_WORDS = {
    "okay": BackchannelKind.ACKNOWLEDGE,
    "mhm": BackchannelKind.CONTINUER,
    "what": BackchannelKind.REPAIR,
}


def classify_planted_backchannel(text: str) -> BackchannelKind:
    """Look up a deliberately scripted backchannel label."""
    try:
        return _BACKCHANNEL_WORDS[text.strip().lower()]
    except KeyError as error:
        raise ValueError(f"unrecognized planted backchannel: {text!r}") from error


def tutorial_scenario(seed: int = 0) -> DialogueScenario:
    """Build a tutorial exchange with a planted clarification and answer."""
    subjects = ("arrays", "loops", "functions")
    subject = subjects[seed % len(subjects)]
    return DialogueScenario(
        "tutorial",
        seed,
        (
            TurnAnnotation("learner", 0, 520, f"explain {subject}", topic=subject),
            TurnAnnotation("tutor", 720, 1_420, f"scripted lesson about {subject}", topic=subject),
            TurnAnnotation("learner", 1_640, 1_940, "show one step", topic=subject),
            TurnAnnotation("tutor", 2_130, 2_700, "scripted worked step", topic=subject),
        ),
    )


def negotiation_scenario(seed: int = 0) -> DialogueScenario:
    """Build a negotiation with a deliberately contested floor interval."""
    amount = 40 + 5 * (seed % 4)
    return DialogueScenario(
        "negotiation",
        seed,
        (
            TurnAnnotation("buyer", 0, 700, f"offer {amount}", topic="price"),
            TurnAnnotation(
                "seller", 880, 1_700, "that is below the scripted target", topic="price"
            ),
            TurnAnnotation("buyer", 1_300, 1_620, "let me finish", "interrupt", "price"),
            TurnAnnotation("seller", 1_900, 2_350, "counter offer", topic="price"),
        ),
    )


EXPANDED_SCENARIOS = {
    "negotiation": negotiation_scenario,
    "tutorial": tutorial_scenario,
}


def make_expanded_scenario(name: str, seed: int = 0) -> DialogueScenario:
    """Resolve an expanded planted scenario by its stable catalog name."""
    try:
        return EXPANDED_SCENARIOS[name](seed)
    except KeyError as error:
        choices = ", ".join(sorted(EXPANDED_SCENARIOS))
        raise ValueError(f"unknown expanded scenario {name!r}; choose from {choices}") from error


@dataclass(frozen=True, slots=True)
class PlantedMishearing:
    """Known substitution attached to a synthetic noisy-channel turn."""

    turn_index: int
    expected: str
    observed: str

    def __post_init__(self) -> None:
        if self.turn_index < 0 or not self.expected or not self.observed:
            raise ValueError("mishearing requires a turn index and nonempty forms")
        if self.expected == self.observed:
            raise ValueError("mishearing forms must differ")


@dataclass(frozen=True, slots=True)
class NoisyChannelScenario:
    dialogue: DialogueScenario
    mishearings: tuple[PlantedMishearing, ...]


def noisy_channel_scenario(seed: int = 0) -> NoisyChannelScenario:
    """Build a repair exchange with an explicit planted transcription error."""
    expected, observed = (("fifteen", "fifty"), ("monday", "sunday"))[seed % 2]
    dialogue = DialogueScenario(
        "noisy-channel",
        seed,
        (
            TurnAnnotation("a", 0, 600, f"I said {expected}", topic="repair"),
            TurnAnnotation("b", 800, 1_260, f"did you say {observed}", topic="repair"),
            TurnAnnotation("a", 1_470, 1_850, f"no {expected}", topic="repair"),
        ),
    )
    return NoisyChannelScenario(dialogue, (PlantedMishearing(1, expected, observed),))


def topic_drift_scenario(seed: int = 0) -> DialogueScenario:
    """Build a dialogue whose planted topic changes twice."""
    rotations = (
        ("travel", "food", "music"),
        ("study", "weather", "books"),
    )
    topics = rotations[seed % len(rotations)]
    turns = tuple(
        TurnAnnotation(
            "a" if index % 2 == 0 else "b",
            index * 620,
            index * 620 + 420,
            f"scripted remark about {topic}",
            topic=topic,
        )
        for index, topic in enumerate((*topics, topics[-1]))
    )
    return DialogueScenario("topic-drift", seed, turns)
