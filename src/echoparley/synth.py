"""Clearly synthetic speech-like signals and planted dialogue structures."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from echoparley.audio import AudioBuffer

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SpeakerProfile:
    """Parameters for a synthetic harmonic signal, not a voice identity."""

    name: str
    fundamental_hz: float
    formants_hz: tuple[float, ...]
    amplitude: float = 0.25

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("speaker name cannot be empty")
        if self.fundamental_hz <= 0 or any(value <= 0 for value in self.formants_hz):
            raise ValueError("synthetic frequencies must be positive")
        if not 0 < self.amplitude <= 1:
            raise ValueError("synthetic amplitude must be in (0, 1]")


def synthesize_formants(
    profile: SpeakerProfile, duration_seconds: float, sample_rate: int, *, seed: int = 0
) -> AudioBuffer:
    """Generate a seeded harmonic-plus-formant fixture with gentle envelopes."""
    if duration_seconds < 0 or sample_rate <= 0:
        raise ValueError("duration must be non-negative and sample_rate positive")
    sample_count = round(duration_seconds * sample_rate)
    if sample_count == 0:
        return AudioBuffer(np.array([], dtype=np.float64), sample_rate)
    time = np.arange(sample_count, dtype=np.float64) / sample_rate
    signal = np.sin(2 * np.pi * profile.fundamental_hz * time)
    for index, frequency in enumerate(profile.formants_hz, 1):
        signal += np.sin(2 * np.pi * frequency * time) / (index + 1)
    rng = np.random.default_rng(seed)
    signal += rng.normal(0.0, 0.01, sample_count)
    ramp = min(sample_count // 2, max(1, round(0.01 * sample_rate)))
    envelope = np.ones(sample_count)
    envelope[:ramp] = np.linspace(0.0, 1.0, ramp, endpoint=False)
    envelope[-ramp:] = np.linspace(1.0, 0.0, ramp, endpoint=False)
    signal *= envelope * profile.amplitude / max(1.0, np.max(np.abs(signal)))
    return AudioBuffer(signal, sample_rate)


TURN_KINDS = frozenset({"turn", "backchannel", "interrupt", "hold"})


@dataclass(frozen=True, slots=True)
class TurnAnnotation:
    """Ground-truth interval deliberately planted by a scenario template."""

    speaker: str
    start_ms: int
    end_ms: int
    text: str
    kind: str = "turn"
    topic: str | None = None

    def __post_init__(self) -> None:
        if not self.speaker or self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("turn requires a speaker and a positive interval")
        if self.kind not in TURN_KINDS:
            raise ValueError(f"unknown turn kind: {self.kind}")


@dataclass(frozen=True, slots=True)
class DialogueScenario:
    """A reproducible script for up to three speakers with planted ground truth."""

    name: str
    seed: int
    turns: tuple[TurnAnnotation, ...]

    def __post_init__(self) -> None:
        if not self.name or self.seed < 0 or not self.turns:
            raise ValueError("scenario requires a name, non-negative seed, and turns")
        if len({turn.speaker for turn in self.turns}) > 3:
            raise ValueError("synthetic dialogue supports at most three speakers")
        if tuple(sorted(self.turns, key=lambda turn: (turn.start_ms, turn.end_ms))) != self.turns:
            raise ValueError("scenario turns must be sorted by start time")

    @property
    def duration_ms(self) -> int:
        return max(turn.end_ms for turn in self.turns)

    def overlaps(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            (left, right)
            for left, first in enumerate(self.turns)
            for right, second in enumerate(self.turns[left + 1 :], left + 1)
            if first.speaker != second.speaker and second.start_ms < first.end_ms
        )


def booking_scenario(seed: int = 0) -> DialogueScenario:
    """Create a short synthetic booking exchange with a floor-holding pause."""
    cities = ("Harbor", "Summit", "Riverside")
    city = cities[seed % len(cities)]
    return DialogueScenario(
        "booking",
        seed,
        (
            TurnAnnotation("a", 0, 700, f"book a ticket to {city}", topic="booking"),
            TurnAnnotation("b", 900, 1_300, "which day", topic="booking"),
            TurnAnnotation("a", 1_500, 1_800, "let me check", "hold", "booking"),
            TurnAnnotation("a", 2_050, 2_450, "next monday", topic="booking"),
        ),
    )


def question_scenario(seed: int = 0) -> DialogueScenario:
    """Create a synthetic question-and-answer structure with planted topics."""
    topics = ("music", "weather", "books")
    topic = topics[seed % len(topics)]
    return DialogueScenario(
        "question",
        seed,
        (
            TurnAnnotation("a", 0, 500, f"tell me about {topic}", topic=topic),
            TurnAnnotation("b", 720, 1_500, f"a scripted answer about {topic}", topic=topic),
            TurnAnnotation("a", 1_720, 2_000, "thanks", topic=topic),
        ),
    )


def barge_in_scenario(seed: int = 0) -> DialogueScenario:
    """Create a deliberate interruption while the other speaker holds the floor."""
    offset = seed % 40
    return DialogueScenario(
        "barge-in",
        seed,
        (
            TurnAnnotation("a", 0, 1_200, "a deliberately long synthetic response", topic="stress"),
            TurnAnnotation("b", 650 + offset, 950 + offset, "please stop", "interrupt", "stress"),
            TurnAnnotation("a", 1_250, 1_500, "acknowledged", topic="stress"),
        ),
    )


def backchannel_scenario(seed: int = 0) -> DialogueScenario:
    """Create short listener acknowledgements inside a long planted turn."""
    word = ("mhm", "okay")[seed % 2]
    return DialogueScenario(
        "backchannel",
        seed,
        (
            TurnAnnotation("a", 0, 1_600, "a long scripted explanation", topic="explanation"),
            TurnAnnotation("b", 400, 520, word, "backchannel", "explanation"),
            TurnAnnotation("b", 1_050, 1_170, word, "backchannel", "explanation"),
        ),
    )


SCENARIO_FACTORIES = {
    "backchannel": backchannel_scenario,
    "barge-in": barge_in_scenario,
    "booking": booking_scenario,
    "question": question_scenario,
}


def make_scenario(name: str, seed: int = 0) -> DialogueScenario:
    """Resolve a built-in scenario by its stable public name."""
    try:
        return SCENARIO_FACTORIES[name](seed)
    except KeyError as error:
        choices = ", ".join(sorted(SCENARIO_FACTORIES))
        raise ValueError(f"unknown scenario {name!r}; choose from {choices}") from error


def render_dialogue(
    scenario: DialogueScenario,
    profiles: dict[str, SpeakerProfile],
    sample_rate: int = 8_000,
) -> dict[str, AudioBuffer]:
    """Render each speaker on an independent channel using planted intervals."""
    missing = {turn.speaker for turn in scenario.turns} - profiles.keys()
    if missing:
        raise ValueError(f"missing speaker profiles: {', '.join(sorted(missing))}")
    sample_count = round(scenario.duration_ms * sample_rate / 1000)
    channels = {speaker: np.zeros(sample_count) for speaker in profiles}
    for index, turn in enumerate(scenario.turns):
        start = round(turn.start_ms * sample_rate / 1000)
        end = round(turn.end_ms * sample_rate / 1000)
        clip = synthesize_formants(
            profiles[turn.speaker],
            (end - start) / sample_rate,
            sample_rate,
            seed=scenario.seed + index,
        )
        channels[turn.speaker][start:end] += clip.samples
    return {
        speaker: AudioBuffer(np.clip(values, -1, 1), sample_rate)
        for speaker, values in channels.items()
    }
