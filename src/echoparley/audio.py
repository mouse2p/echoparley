"""Thin NumPy audio conventions and PCM WAV transport."""

from __future__ import annotations

import io
import wave
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class AudioBuffer:
    """Finite mono samples normalized to the closed interval [-1, 1]."""

    samples: FloatArray
    sample_rate: int

    def __post_init__(self) -> None:
        samples = np.asarray(self.samples, dtype=np.float64)
        if samples.ndim != 1:
            raise ValueError("audio samples must be one-dimensional mono")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if not np.all(np.isfinite(samples)):
            raise ValueError("audio samples must be finite")
        if samples.size and np.max(np.abs(samples)) > 1.0:
            raise ValueError("audio samples must be normalized to [-1, 1]")
        samples = samples.copy()
        samples.setflags(write=False)
        object.__setattr__(self, "samples", samples)

    @property
    def duration_seconds(self) -> float:
        return len(self.samples) / self.sample_rate


def encode_pcm16(samples: FloatArray, *, clip: bool = False) -> bytes:
    """Encode normalized mono samples, optionally clipping out-of-range values."""
    values = np.asarray(samples, dtype=np.float64)
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise ValueError("PCM input must be a finite one-dimensional array")
    if not clip and values.size and np.max(np.abs(values)) > 1.0:
        raise ValueError("PCM input exceeds normalized range")
    clipped = np.clip(values, -1.0, 1.0)
    integers = np.where(clipped < 0, clipped * 32768.0, clipped * 32767.0)
    return np.rint(integers).astype("<i2").tobytes()


def decode_pcm16(data: bytes) -> FloatArray:
    """Decode little-endian signed PCM16 into normalized float samples."""
    if len(data) % 2:
        raise ValueError("PCM16 data length must be even")
    integers = np.frombuffer(data, dtype="<i2").astype(np.float64)
    return np.where(integers < 0, integers / 32768.0, integers / 32767.0)


def write_wav(buffer: AudioBuffer) -> bytes:
    """Serialize a mono buffer to a standards-compatible PCM16 WAV."""
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(buffer.sample_rate)
        wav.writeframes(encode_pcm16(buffer.samples))
    return output.getvalue()


def read_wav(data: bytes) -> AudioBuffer:
    """Read mono PCM16 WAV bytes under the package audio convention."""
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            if wav.getnchannels() != 1:
                raise ValueError("WAV must be mono")
            if wav.getsampwidth() != 2 or wav.getcomptype() != "NONE":
                raise ValueError("WAV must contain uncompressed PCM16")
            sample_rate = wav.getframerate()
            frames = wav.readframes(wav.getnframes())
    except (EOFError, wave.Error) as error:
        raise ValueError(f"invalid WAV data: {error}") from error
    return AudioBuffer(decode_pcm16(frames), sample_rate)


def frame_audio(
    samples: FloatArray, frame_size: int, hop_size: int, *, pad_end: bool = False
) -> FloatArray:
    """Return copied frames, optionally zero-padding the final partial frame."""
    values = np.asarray(samples, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("framing input must be one-dimensional")
    if frame_size <= 0 or hop_size <= 0:
        raise ValueError("frame_size and hop_size must be positive")
    if values.size < frame_size:
        count = 1 if pad_end and values.size else 0
    else:
        remainder = values.size - frame_size
        count = 1 + remainder // hop_size
        if pad_end and remainder % hop_size:
            count += 1
    result = np.zeros((count, frame_size), dtype=np.float64)
    for index in range(count):
        chunk = values[index * hop_size : index * hop_size + frame_size]
        result[index, : len(chunk)] = chunk
    return result


@dataclass(frozen=True, slots=True)
class FrameSpan:
    """Half-open sample interval represented by one analysis frame."""

    index: int
    start_sample: int
    end_sample: int

    def __post_init__(self) -> None:
        if self.index < 0 or self.start_sample < 0 or self.end_sample < self.start_sample:
            raise ValueError("invalid frame span")


def frame_spans(
    sample_count: int, frame_size: int, hop_size: int, *, pad_end: bool = False
) -> tuple[FrameSpan, ...]:
    """Describe exact source coverage for every frame returned by ``frame_audio``."""
    if sample_count < 0:
        raise ValueError("sample_count must be non-negative")
    frames = frame_audio(np.zeros(sample_count), frame_size, hop_size, pad_end=pad_end)
    return tuple(
        FrameSpan(index, index * hop_size, min(index * hop_size + frame_size, sample_count))
        for index in range(len(frames))
    )
