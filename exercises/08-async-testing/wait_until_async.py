"""Async variants of Session 08 polling. Cancellation always propagates."""
from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import TypeVar

from wait_until import Attempt, ObservationUnavailable, WaitTimeout, _validate

T = TypeVar("T")


async def wait_until_async(
    predicate: Callable[[], Awaitable[T]], *, timeout: float = 10.0,
    interval: float = 0.2, clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    return await wait_until_async_diagnostic(
        predicate, timeout=timeout, interval=interval, clock=clock, sleep=sleep
    )


async def wait_until_async_diagnostic(
    predicate: Callable[[], Awaitable[T]], *, timeout: float = 10.0,
    interval: float = 0.2, retry_exceptions: tuple[type[Exception], ...] = (),
    history_limit: int = 20, clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
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
            result = await predicate()
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
        await sleep(min(interval, remaining))
    message = (f"wait_until_async timeout: attempts={attempts}, elapsed={clock()-start:.3f}s, "
               f"successful_reads={successful_reads}, errors={errors}, last_value={last_value!r}")
    cls = ObservationUnavailable if errors and not successful_reads else WaitTimeout
    raise cls(message, attempts=attempts, last_value=last_value,
              errors=errors, history=tuple(history)) from last_error
