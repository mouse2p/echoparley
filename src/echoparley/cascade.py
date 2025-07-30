"""Explicit STT-to-text-LM-to-TTS comparison path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class TextStage(Protocol):
    def __call__(self, value: str) -> str: ...


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
