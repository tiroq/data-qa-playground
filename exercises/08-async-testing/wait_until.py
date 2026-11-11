"""Session 08 reference implementations: synchronous polling.

Soft deadline: never START a new predicate after deadline, but accept a
successful call that started before the deadline and finished later.
"""
from __future__ import annotations

import math
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Attempt:
    number: int
    elapsed: float
    value: object | None = None
    error: str | None = None


class WaitTimeout(TimeoutError):
    def __init__(self, message: str, *, attempts: int, last_value: object | None,
                 errors: int, history: tuple[Attempt, ...]):
        super().__init__(message)
        self.attempts = attempts
        self.last_value = last_value
        self.errors = errors
        self.history = history


class ObservationUnavailable(WaitTimeout):
    """Every observation attempt failed with a permitted transient exception."""


def _validate(timeout: float, interval: float,
              retry_exceptions: tuple[type[Exception], ...], history_limit: int) -> None:
    if not math.isfinite(timeout) or timeout < 0:
        raise ValueError("timeout must be finite and non-negative")
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("interval must be finite and positive")
    if not isinstance(retry_exceptions, tuple) or any(
        not isinstance(e, type) or not issubclass(e, Exception)
        for e in retry_exceptions
    ):
        raise TypeError("retry_exceptions must be a tuple of Exception subclasses")
    if isinstance(history_limit, bool) or not isinstance(history_limit, int) or history_limit < 1:
        raise ValueError("history_limit must be a positive integer")


def wait_until(predicate: Callable[[], T], *, timeout: float = 10.0,
               interval: float = 0.2, clock: Callable[[], float] = time.monotonic,
               sleep: Callable[[float], None] = time.sleep) -> T:
    """Basic wait: no exception retries and no diagnostic history."""
    return wait_until_diagnostic(predicate, timeout=timeout, interval=interval,
                                 clock=clock, sleep=sleep)


def wait_until_diagnostic(
    predicate: Callable[[], T], *, timeout: float = 10.0, interval: float = 0.2,
    retry_exceptions: tuple[type[Exception], ...] = (),
    history_limit: int = 20, clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Poll truthy predicate with bounded sleeping and bounded diagnostic history.

    Timeout=0 permits one initial observation at start, not an unbounded loop.
    Non-retryable errors and cancellation propagate immediately.
    """
    _validate(timeout, interval, retry_exceptions, history_limit)
    start = clock()
    deadline = start + timeout
    history: deque[Attempt] = deque(maxlen=history_limit)
    attempts = errors = successful_reads = 0
    last_value: object | None = None
    last_error: Exception | None = None
    while True:
        if attempts and clock() >= deadline:
            break
        attempts += 1
        try:
            result = predicate()
        except retry_exceptions as exc:
            errors += 1
            last_error = exc
            history.append(Attempt(attempts, clock() - start, error=f"{type(exc).__name__}: {exc}"))
        else:
            successful_reads += 1
            last_value = result
            history.append(Attempt(attempts, clock() - start, value=result))
            if result:
                return result
        remaining = deadline - clock()
        if remaining <= 0:
            break
        sleep(min(interval, remaining))
    message = (f"wait_until timeout: attempts={attempts}, elapsed={clock()-start:.3f}s, "
               f"successful_reads={successful_reads}, errors={errors}, last_value={last_value!r}")
    cls = ObservationUnavailable if errors and not successful_reads else WaitTimeout
    raise cls(message, attempts=attempts, last_value=last_value,
              errors=errors, history=tuple(history)) from last_error
