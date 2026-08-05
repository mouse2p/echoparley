"""Expanded planted scenarios for the synthetic dialogue laboratory."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from echoparley.artifacts import ArtifactEnvelope, content_checksum, decode_jsonl, encode_jsonl
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


def validate_scenario_annotations(
    scenario: DialogueScenario, annotations: ScenarioAnnotations
) -> None:
    """Reject supplemental labels that do not point at matching planted turns."""
    for index, kind in annotations.backchannels:
        if index >= len(scenario.turns) or scenario.turns[index].kind != "backchannel":
            raise ValueError("backchannel annotation must reference a backchannel turn")
        if classify_planted_backchannel(scenario.turns[index].text) is not kind:
            raise ValueError("backchannel annotation conflicts with planted text")


def scenario_manifest(
    scenario: DialogueScenario, annotations: ScenarioAnnotations | None = None
) -> dict[str, object]:
    """Encode complete planted dialogue ground truth using manifest schema 2.0."""
    labels = dict((annotations or ScenarioAnnotations()).backchannels)
    return {
        "schema_version": "2.0",
        "name": scenario.name,
        "seed": scenario.seed,
        "speakers": sorted({turn.speaker for turn in scenario.turns}),
        "turns": [
            {
                "speaker": turn.speaker,
                "start_ms": turn.start_ms,
                "end_ms": turn.end_ms,
                "text": turn.text,
                "kind": turn.kind,
                "topic": turn.topic,
                "backchannel_kind": labels[index].value if index in labels else None,
            }
            for index, turn in enumerate(scenario.turns)
        ],
    }


def scenario_manifest_envelope(
    scenario: DialogueScenario, annotations: ScenarioAnnotations | None = None
) -> ArtifactEnvelope:
    """Wrap schema-2 planted ground truth in a checksummed artifact envelope."""
    return ArtifactEnvelope.create(
        "dialogue-scenario", scenario_manifest(scenario, annotations), "2.0"
    )


def encode_scenario_corpus(
    records: tuple[tuple[DialogueScenario, ScenarioAnnotations | None], ...],
) -> bytes:
    """Encode a nonempty ordered corpus of planted scenario manifests."""
    if not records:
        raise ValueError("scenario corpus cannot be empty")
    names = tuple(scenario.name for scenario, _ in records)
    if len(names) != len(set(names)):
        raise ValueError("scenario corpus names must be unique")
    return encode_jsonl(
        scenario_manifest_envelope(scenario, annotations) for scenario, annotations in records
    )


def decode_scenario_corpus(
    data: bytes,
) -> tuple[tuple[DialogueScenario, ScenarioAnnotations], ...]:
    """Decode schema-2 scenario artifacts and restore their typed annotations."""
    envelopes = decode_jsonl(data)
    if not envelopes or any(
        item.kind != "dialogue-scenario" or item.schema_version != "2.0" for item in envelopes
    ):
        raise ValueError("scenario corpus contains an unsupported artifact")
    decoded = tuple(scenario_from_manifest(item.payload) for item in envelopes)
    names = tuple(scenario.name for scenario, _ in decoded)
    if len(names) != len(set(names)):
        raise ValueError("scenario corpus names must be unique")
    return decoded


def migrate_scenario_manifest(value: dict[str, object]) -> dict[str, object]:
    """Upgrade a trusted schema-1 manifest to schema 2 without changing turns."""
    if value.get("schema_version") == "2.0":
        return value
    if value.get("schema_version") != "1.0" or not isinstance(value.get("turns"), list):
        raise ValueError("unsupported dialogue manifest schema")
    migrated = {**value, "schema_version": "2.0"}
    turns = [{**turn, "backchannel_kind": None} for turn in value["turns"]]
    migrated["turns"] = turns
    migrated["speakers"] = sorted({str(turn["speaker"]) for turn in turns})
    return migrated


def scenario_from_manifest(
    value: dict[str, object],
) -> tuple[DialogueScenario, ScenarioAnnotations]:
    """Restore and validate a dialogue plus supplemental labels from schema 2."""
    manifest = migrate_scenario_manifest(value)
    if set(manifest) != {"schema_version", "name", "seed", "speakers", "turns"}:
        raise ValueError("dialogue manifest fields do not match schema 2")
    raw_turns = manifest["turns"]
    if not isinstance(raw_turns, list):
        raise TypeError("dialogue manifest turns must be a list")
    turns = tuple(
        TurnAnnotation(
            str(item["speaker"]),
            int(item["start_ms"]),
            int(item["end_ms"]),
            str(item["text"]),
            str(item["kind"]),
            item["topic"],
        )
        for item in raw_turns
    )
    labels = tuple(
        (index, BackchannelKind(item["backchannel_kind"]))
        for index, item in enumerate(raw_turns)
        if item["backchannel_kind"] is not None
    )
    scenario = DialogueScenario(str(manifest["name"]), int(manifest["seed"]), turns)
    annotations = ScenarioAnnotations(labels)
    validate_scenario_annotations(scenario, annotations)
    if sorted({turn.speaker for turn in turns}) != manifest["speakers"]:
        raise ValueError("dialogue manifest speaker index does not match turns")
    return scenario, annotations


@dataclass(frozen=True, slots=True)
class CorpusStatistics:
    dialogues: int
    turns: int
    speakers: int
    overlaps: int
    backchannels: int
    duration_ms: int


def corpus_statistics(scenarios: tuple[DialogueScenario, ...]) -> CorpusStatistics:
    """Aggregate transparent counts over a synthetic scenario collection."""
    if not scenarios:
        raise ValueError("corpus statistics require at least one scenario")
    return CorpusStatistics(
        len(scenarios),
        sum(len(item.turns) for item in scenarios),
        len({turn.speaker for item in scenarios for turn in item.turns}),
        sum(len(item.overlaps()) for item in scenarios),
        sum(turn.kind == "backchannel" for item in scenarios for turn in item.turns),
        sum(item.duration_ms for item in scenarios),
    )


def corpus_report(scenarios: tuple[DialogueScenario, ...]) -> dict[str, object]:
    """Build a checksummed report whose measurements are synthetic counts."""
    statistics = corpus_statistics(scenarios)
    payload = {
        "data_origin": "synthetic-planted",
        "dialogues": statistics.dialogues,
        "turns": statistics.turns,
        "speakers": statistics.speakers,
        "overlaps": statistics.overlaps,
        "backchannels": statistics.backchannels,
        "duration_ms": statistics.duration_ms,
    }
    return {**payload, "checksum": content_checksum(payload)}


def scenario_catalog(seed: int = 0) -> dict[str, DialogueScenario]:
    """Return all expanded Phase 2 scenarios at one reproducible seed."""
    noisy = noisy_channel_scenario(seed).dialogue
    scenarios = (
        tutorial_scenario(seed),
        negotiation_scenario(seed),
        noisy,
        topic_drift_scenario(seed),
        casual_backchannel_scenario(seed),
        three_speaker_scenario(seed),
    )
    return {scenario.name: scenario for scenario in scenarios}


def long_topic_scenario(seed: int = 0, turn_count: int = 30) -> DialogueScenario:
    """Generate a long two-speaker history with sparse planted target-topic turns."""
    if turn_count <= 0:
        raise ValueError("long scenario turn count must be positive")
    topics = ("target", "travel", "music", "study")
    turns = tuple(
        TurnAnnotation(
            ("a", "b")[index % 2],
            index * 220,
            index * 220 + 160,
            f"synthetic long turn {index}",
            topic=topics[0] if index % 7 == seed % 7 else topics[1 + index % 3],
        )
        for index in range(turn_count)
    )
    return DialogueScenario("long-topic", seed, turns)
