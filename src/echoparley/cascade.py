"""Explicit STT-to-text-LM-to-TTS comparison path."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from echoparley.adapters import AdapterAction
from echoparley.events import EndpointEvent
from echoparley.stream import UnifiedStream


class TextStage(Protocol):
    def __call__(self, value: str) -> str: ...


@dataclass(frozen=True, slots=True)
class VoiceActivitySpan:
    start_frame: int
    end_frame: int


@dataclass(frozen=True, slots=True)
class MockVAD:
    """Energy threshold stage for offline synthetic fixtures."""

    threshold: float = 0.05

    def __post_init__(self) -> None:
        if self.threshold < 0:
            raise ValueError("VAD threshold must be non-negative")

    def __call__(self, frame_energy: NDArray[np.float64]) -> tuple[VoiceActivitySpan, ...]:
        values = np.asarray(frame_energy, dtype=np.float64)
        if values.ndim != 1 or not np.all(np.isfinite(values)):
            raise ValueError("VAD energy must be a finite vector")
        active = values >= self.threshold
        boundaries = np.flatnonzero(np.diff(np.concatenate(([False], active, [False]))))
        return tuple(
            VoiceActivitySpan(int(start), int(end)) for start, end in boundaries.reshape(-1, 2)
        )


@dataclass(frozen=True, slots=True)
class CascadeResult:
    transcript: str
    response: str
    units: tuple[int, ...]
    stage_delays_ms: tuple[int, int, int]

    @property
    def total_delay_ms(self) -> int:
        return sum(self.stage_delays_ms)


@dataclass(frozen=True, slots=True)
class ScriptedCascade:
    stt: TextStage
    text_lm: TextStage
    tts: TextStage
    stage_delays_ms: tuple[int, int, int] = (80, 60, 90)

    def run(self, audio_label: str) -> CascadeResult:
        transcript = self.stt(audio_label)
        response = self.text_lm(transcript)
        encoded = self.tts(response)
        return CascadeResult(
            transcript,
            response,
            tuple(ord(character) % 32 for character in encoded),
            self.stage_delays_ms,
        )

    def __post_init__(self) -> None:
        if any(delay < 0 for delay in self.stage_delays_ms):
            raise ValueError("cascade stage delays must be non-negative")


def compare_paths(
    cascade: CascadeResult, direct_delay_ms: int, direct_units: tuple[int, ...]
) -> dict[str, int | str]:
    """Compare measured synthetic path latency and unit counts."""
    if direct_delay_ms < 0:
        raise ValueError("direct delay must be non-negative")
    winner = (
        "direct"
        if direct_delay_ms < cascade.total_delay_ms
        else "cascade"
        if cascade.total_delay_ms < direct_delay_ms
        else "tie"
    )
    return {
        "cascade_ms": cascade.total_delay_ms,
        "direct_ms": direct_delay_ms,
        "latency_winner": winner,
        "cascade_units": len(cascade.units),
        "direct_units": len(direct_units),
    }


@dataclass(slots=True)
class CascadeAdapter:
    cascade: ScriptedCascade
    latest_label: str = "silence"

    def observe(self, value: UnifiedStream) -> None:
        self.latest_label = " ".join(token.value for token in value.tokens)

    def act(self, events: tuple[EndpointEvent, ...]) -> AdapterAction:
        del events
        result = self.cascade.run(self.latest_label)
        return AdapterAction(
            tuple(f"<unit:{unit}>" for unit in result.units), result.total_delay_ms
        )


@dataclass(frozen=True, slots=True)
class MockPunctuation:
    """Deterministic transcript casing and terminal punctuation stage."""

    terminal: str = "."

    def __post_init__(self) -> None:
        if self.terminal not in {".", "?", "!"}:
            raise ValueError("unsupported terminal punctuation")

    def __call__(self, value: str) -> str:
        text = " ".join(value.split())
        if not text:
            return ""
        restored = text[0].upper() + text[1:]
        return restored if restored[-1] in ".?!" else restored + self.terminal


@dataclass(frozen=True, slots=True)
class AlignedTTSUnit:
    identifier: int
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True, slots=True)
class MockTTSAlignment:
    unit_ms: int = 40

    def __post_init__(self) -> None:
        if self.unit_ms <= 0:
            raise ValueError("TTS unit duration must be positive")

    def __call__(self, text: str) -> tuple[AlignedTTSUnit, ...]:
        words = text.split()
        return tuple(
            AlignedTTSUnit(
                sum(map(ord, word)) % 64, index * self.unit_ms, (index + 1) * self.unit_ms, word
            )
            for index, word in enumerate(words)
        )


@dataclass(frozen=True, slots=True)
class StageTiming:
    name: str
    delay_ms: int

    def __post_init__(self) -> None:
        if not self.name or self.delay_ms < 0:
            raise ValueError("stage timing requires a name and non-negative delay")


@dataclass(frozen=True, slots=True)
class StageLatencyLedger:
    timings: tuple[StageTiming, ...] = ()

    @property
    def total_ms(self) -> int:
        return sum(item.delay_ms for item in self.timings)

    def append(self, name: str, delay_ms: int) -> StageLatencyLedger:
        return StageLatencyLedger((*self.timings, StageTiming(name, delay_ms)))


@dataclass(frozen=True, slots=True)
class SeededFaultPlan:
    seed: int
    failure_rate: float
    stages: tuple[str, ...] = ("vad", "stt", "punctuation", "lm", "tts")

    def __post_init__(self) -> None:
        if (
            self.seed < 0
            or not 0 <= self.failure_rate <= 1
            or not self.stages
            or any(not item for item in self.stages)
        ):
            raise ValueError("fault plan configuration is invalid")

    def failing_stages(self) -> frozenset[str]:
        rng = random.Random(self.seed)
        return frozenset(stage for stage in self.stages if rng.random() < self.failure_rate)


@dataclass(frozen=True, slots=True)
class CascadeDegradation:
    failed_stage: str
    fallback: str
    retained_output: str


def degrade_after_failure(stage: str, last_output: str) -> CascadeDegradation:
    """Choose an explicit local fallback without pretending the stage succeeded."""
    fallbacks = {
        "vad": "treat-as-silence",
        "stt": "empty-transcript",
        "punctuation": "raw-transcript",
        "lm": "scripted-apology",
        "tts": "text-only-response",
    }
    if stage not in fallbacks:
        raise ValueError(f"unknown cascade stage: {stage}")
    retained = last_output if stage in {"punctuation", "tts"} else ""
    return CascadeDegradation(stage, fallbacks[stage], retained)


CASCADE_STAGE_ORDER = ("vad", "stt", "punctuation", "lm", "tts")


@dataclass(frozen=True, slots=True)
class CascadeConfiguration:
    enabled_stages: tuple[str, ...] = CASCADE_STAGE_ORDER
    delays_ms: tuple[int, ...] = (10, 80, 15, 60, 90)

    def __post_init__(self) -> None:
        if not self.enabled_stages or len(self.enabled_stages) != len(self.delays_ms):
            raise ValueError("cascade stages and delays must align")
        if any(stage not in CASCADE_STAGE_ORDER for stage in self.enabled_stages) or len(
            set(self.enabled_stages)
        ) != len(self.enabled_stages):
            raise ValueError("cascade stages must be known and unique")
        positions = [CASCADE_STAGE_ORDER.index(stage) for stage in self.enabled_stages]
        if positions != sorted(positions) or any(delay < 0 for delay in self.delays_ms):
            raise ValueError("cascade stages must follow pipeline order with non-negative delays")

    def with_delay(self, stage: str, delay_ms: int) -> CascadeConfiguration:
        """Return a validated copy with one stage delay replaced."""
        if stage not in self.enabled_stages:
            raise ValueError(f"stage is not enabled: {stage}")
        delays = list(self.delays_ms)
        delays[self.enabled_stages.index(stage)] = delay_ms
        return replace(self, delays_ms=tuple(delays))

    def latency_ledger(self) -> StageLatencyLedger:
        return StageLatencyLedger(
            tuple(
                StageTiming(name, delay)
                for name, delay in zip(self.enabled_stages, self.delays_ms, strict=True)
            )
        )


@dataclass(frozen=True, slots=True)
class StageObservation:
    """Compact observable input/output labels for one mock pipeline stage."""

    stage: str
    input_label: str
    output_label: str
    delay_ms: int

    def __post_init__(self) -> None:
        if self.stage not in CASCADE_STAGE_ORDER or self.delay_ms < 0:
            raise ValueError("stage observation is invalid")


@dataclass(frozen=True, slots=True)
class CascadeExecution:
    """Outputs, timing, and optional failure from one local mock cascade."""

    observations: tuple[StageObservation, ...]
    ledger: StageLatencyLedger
    transcript: str
    response: str
    aligned_units: tuple[AlignedTTSUnit, ...]
    degradation: CascadeDegradation | None = None

    @property
    def succeeded(self) -> bool:
        return self.degradation is None


def execute_mock_cascade(
    frame_energy: NDArray[np.float64],
    transcript: str,
    response: str,
    *,
    configuration: CascadeConfiguration | None = None,
) -> CascadeExecution:
    """Run configured local mock stages and retain observable intermediate labels."""
    config = configuration or CascadeConfiguration()
    observations: list[StageObservation] = []
    current_transcript = transcript.strip()
    current_response = response.strip()
    aligned: tuple[AlignedTTSUnit, ...] = ()
    for stage, delay in zip(config.enabled_stages, config.delays_ms, strict=True):
        before = current_transcript if stage in {"punctuation", "lm"} else stage
        if stage == "vad":
            spans = MockVAD()(frame_energy)
            after = f"{len(spans)} speech spans"
        elif stage == "stt":
            after = current_transcript
        elif stage == "punctuation":
            current_transcript = MockPunctuation()(current_transcript)
            after = current_transcript
        elif stage == "lm":
            current_response = current_response if current_transcript else ""
            after = current_response
        else:
            aligned = MockTTSAlignment()(current_response)
            after = f"{len(aligned)} aligned units"
        observations.append(StageObservation(stage, before, after, delay))
    return CascadeExecution(
        tuple(observations), config.latency_ledger(), current_transcript, current_response, aligned
    )
