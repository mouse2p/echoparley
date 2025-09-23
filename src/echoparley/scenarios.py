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


class FloorContentionPolicy(StrEnum):
    """Deterministic planted rules for choosing among simultaneous claimants."""

    EARLIEST = "earliest"
    ROUND_ROBIN = "round-robin"
    LONGEST_WAIT = "longest-wait"


def resolve_floor_contention(
    claimants: tuple[tuple[str, int], ...], policy: FloorContentionPolicy, *, turn_index: int = 0
) -> str:
    """Choose a speaker from `(name, waiting_ms)` claims with stable ties."""
    if not claimants or any(not name or wait < 0 for name, wait in claimants):
        raise ValueError("floor contention requires valid claimants")
    if policy is FloorContentionPolicy.EARLIEST:
        return claimants[0][0]
    if policy is FloorContentionPolicy.ROUND_ROBIN:
        return claimants[turn_index % len(claimants)][0]
    return max(claimants, key=lambda item: (item[1], item[0]))[0]


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


def casual_backchannel_scenario(seed: int = 0) -> DialogueScenario:
    """Build a long casual turn with all planted backchannel functions."""
    offset = seed % 30
    return DialogueScenario(
        "casual-backchannel",
        seed,
        (
            TurnAnnotation("a", 0, 2_100, "scripted casual story", topic="story"),
            TurnAnnotation("b", 350 + offset, 470 + offset, "mhm", "backchannel", "story"),
            TurnAnnotation("b", 920 + offset, 1_040 + offset, "okay", "backchannel", "story"),
            TurnAnnotation("b", 1_500 + offset, 1_650 + offset, "what", "backchannel", "story"),
        ),
    )


def scenario_topics(scenario: DialogueScenario, *, collapse: bool = True) -> tuple[str, ...]:
    """Return planted topics in temporal order, optionally collapsing repeats."""
    topics = tuple(turn.topic for turn in scenario.turns if turn.topic is not None)
    if not collapse:
        return topics
    return tuple(
        topic for index, topic in enumerate(topics) if index == 0 or topic != topics[index - 1]
    )


def three_speaker_scenario(seed: int = 0) -> DialogueScenario:
    """Build a three-party exchange with a planted simultaneous floor claim."""
    offset = seed % 25
    return DialogueScenario(
        "three-speaker-contention",
        seed,
        (
            TurnAnnotation("a", 0, 700, "opening statement", topic="planning"),
            TurnAnnotation("b", 900, 1_450, "first proposal", topic="planning"),
            TurnAnnotation(
                "c", 1_180 + offset, 1_620 + offset, "competing proposal", "interrupt", "planning"
            ),
            TurnAnnotation("a", 1_850, 2_300, "scripted resolution", topic="planning"),
        ),
    )


@dataclass(frozen=True, slots=True)
class ScenarioAnnotations:
    """Supplemental planted labels keyed by dialogue turn index."""

    backchannels: tuple[tuple[int, BackchannelKind], ...] = ()

    def __post_init__(self) -> None:
        indices = tuple(index for index, _ in self.backchannels)
        if any(index < 0 for index in indices) or len(indices) != len(set(indices)):
            raise ValueError("backchannel annotation indices must be unique and non-negative")


def casual_backchannel_annotations(scenario: DialogueScenario) -> ScenarioAnnotations:
    """Derive labels only for explicitly planted backchannel turns."""
    labels = tuple(
        (index, classify_planted_backchannel(turn.text))
        for index, turn in enumerate(scenario.turns)
        if turn.kind == "backchannel"
    )
    return ScenarioAnnotations(labels)
