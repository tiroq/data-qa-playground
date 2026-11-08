"""Session 08 learner exercise: implement deterministic async waiting.

Use the supplied ManualClock in tests to avoid real-time delays.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")


class ObservationTimeout(TimeoutError):
    """TODO: include useful attempts/elapsed/last-state diagnostics."""


async def wait_until(
    read: Callable[[], Awaitable[T]],
    is_ready: Callable[[T], bool],
    *,
    timeout: float,
    interval: float,
    monotonic: Callable[[], float],
    sleep: Callable[[float], Awaitable[None]],
    retry_exceptions: tuple[type[Exception], ...] = (),
) -> T:
    """TODO (learner): bounded polling with exception policy and diagnostics."""
    raise NotImplementedError("Session 08: implement wait_until")
