"""Cancellable wall-clock or accelerated session tick loops."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TickConfig:
    interval_ms: int = 20
    accelerated: bool = True

    def __post_init__(self) -> None:
        if self.interval_ms <= 0:
            raise ValueError("tick interval must be positive")


@dataclass(slots=True)
class CancellationToken:
    cancelled: bool = False
    reason: str | None = None

    def cancel(self, reason: str = "cancelled") -> None:
        self.cancelled = True
        self.reason = reason


def run_ticks(
    count: int,
    callback: Callable[[int], object],
    config: TickConfig | None = None,
    cancellation: CancellationToken | None = None,
) -> tuple[int, ...]:
    """Run ticks and return executed logical times, retaining partial progress."""
    config = config or TickConfig()
    if count < 0:
        raise ValueError("tick count must be non-negative")
    cancellation = cancellation or CancellationToken()
    executed: list[int] = []
    for index in range(count):
        if cancellation.cancelled:
            break
        logical_time = index * config.interval_ms
        callback(logical_time)
        executed.append(logical_time)
        if not config.accelerated:
            time.sleep(config.interval_ms / 1000)
    return tuple(executed)


def record_ticks(count: int, config: TickConfig | None = None) -> tuple[object, ...]:
    """Run accelerated ticks into a closed session event tuple."""
    from echoparley.session import SessionRecorder

    config = config or TickConfig()
    recorder = SessionRecorder()
    run_ticks(count, lambda time_ms: recorder.append(time_ms, "tick"), config)
    return recorder.close()
