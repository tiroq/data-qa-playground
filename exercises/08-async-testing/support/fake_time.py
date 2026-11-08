"""Deterministic manual clock and delayed visibility for Session 08.

Infrastructure only. The polling loop under test is the learner's work.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ManualClock:
    now: float = 0.0
    sleeps: list[float] = field(default_factory=list)

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("sleep duration must be nonnegative")
        self.sleeps.append(duration)
        self.now += duration
        # Yield once to keep cancellation/async scheduling observable.
        await asyncio.sleep(0)


@dataclass
class EventuallyVisibleFeed:
    clock: ManualClock
    visible_at: float
    value: Any
    transient_failures: int = 0
    read_count: int = 0

    async def read(self) -> Any | None:
        self.read_count += 1
        if self.read_count <= self.transient_failures:
            raise ConnectionError("synthetic transient read failure")
        return self.value if self.clock.monotonic() >= self.visible_at else None
