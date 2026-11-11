"""Deterministic Session 08 tests. Run: python -m pytest -q exercises/08-async-testing"""
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from wait_until import ObservationUnavailable, WaitTimeout, wait_until, wait_until_diagnostic
from wait_until_async import wait_until_async, wait_until_async_diagnostic


class FakeTime:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    async def async_sleep(self, seconds):
        self.sleep(seconds)


def test_boundary_three_calls_and_bounded_sleep():
    fake = FakeTime()
    calls = []
    def predicate():
        calls.append(fake.now)
        return None
    with pytest.raises(WaitTimeout) as info:
        wait_until(predicate, timeout=1.0, interval=0.4,
                   clock=fake.clock, sleep=fake.sleep)
    assert calls == pytest.approx([0, 0.4, 0.8])
    assert fake.sleeps == pytest.approx([0.4, 0.4, 0.2])
    assert info.value.attempts == 3


def test_success_and_last_value():
    fake = FakeTime()
    values = iter([None, {"status": "PROCESSED"}])
    assert wait_until(lambda: next(values), clock=fake.clock, sleep=fake.sleep) == {
        "status": "PROCESSED"
    }


def test_late_success_from_started_call_is_accepted():
    fake = FakeTime()
    def predicate():
        fake.now += 1.2
        return "done"
    assert wait_until(predicate, timeout=1, clock=fake.clock, sleep=fake.sleep) == "done"


def test_all_connection_errors_are_distinguished():
    fake = FakeTime()
    def fail():
        raise ConnectionError("db unreachable")
    with pytest.raises(ObservationUnavailable) as info:
        wait_until_diagnostic(fail, timeout=0.5, interval=0.2,
                              retry_exceptions=(ConnectionError,),
                              clock=fake.clock, sleep=fake.sleep)
    assert info.value.errors == info.value.attempts
    assert info.value.__cause__.__class__ is ConnectionError


def test_mixed_none_and_transient_errors():
    fake = FakeTime()
    counter = 0
    def predicate():
        nonlocal counter
        counter += 1
        if counter == 1:
            return None
        raise ConnectionError("temporary")
    with pytest.raises(WaitTimeout) as info:
        wait_until_diagnostic(predicate, timeout=0.5, interval=0.2,
                              retry_exceptions=(ConnectionError,),
                              clock=fake.clock, sleep=fake.sleep)
    assert type(info.value) is WaitTimeout
    assert info.value.errors > 0
    assert info.value.last_value is None


def test_transient_recovery_and_fatal_propagation():
    fake = FakeTime()
    counter = 0
    def predicate():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise ConnectionError("temporary")
        return "ready"
    assert wait_until_diagnostic(predicate, retry_exceptions=(ConnectionError,),
                                 clock=fake.clock, sleep=fake.sleep) == "ready"
    with pytest.raises(ValueError, match="invalid query"):
        wait_until_diagnostic(lambda: (_ for _ in ()).throw(ValueError("invalid query")),
                              retry_exceptions=(ConnectionError,),
                              clock=fake.clock, sleep=fake.sleep)


def test_keyboard_interrupt_propagates():
    def interrupted():
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        wait_until_diagnostic(interrupted)


@pytest.mark.parametrize("timeout,interval", [(-1, 0.1), (1, 0), (float("inf"), 0.1)])
def test_invalid_timeouts(timeout, interval):
    with pytest.raises(ValueError):
        wait_until(lambda: None, timeout=timeout, interval=interval)


def test_history_is_bounded():
    fake = FakeTime()
    with pytest.raises(WaitTimeout) as info:
        wait_until_diagnostic(lambda: None, timeout=1, interval=0.1,
                              history_limit=2, clock=fake.clock, sleep=fake.sleep)
    assert len(info.value.history) == 2


@pytest.mark.asyncio
async def test_async_boundary_and_success():
    fake = FakeTime()
    calls = []
    async def predicate():
        calls.append(fake.now)
        return None
    with pytest.raises(WaitTimeout):
        await wait_until_async(predicate, timeout=1, interval=0.4,
                               clock=fake.clock, sleep=fake.async_sleep)
    assert calls == pytest.approx([0, 0.4, 0.8])


@pytest.mark.asyncio
async def test_async_transient_recovery():
    fake = FakeTime()
    attempts = 0
    async def predicate():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("temporary")
        return "ok"
    assert await wait_until_async_diagnostic(
        predicate, retry_exceptions=(ConnectionError,),
        clock=fake.clock, sleep=fake.async_sleep) == "ok"


@pytest.mark.asyncio
async def test_async_cancellation_propagates():
    async def predicate():
        await asyncio.sleep(100)
    task = asyncio.create_task(wait_until_async_diagnostic(predicate))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_stale_reads_are_predicate_responsibility():
    fake = FakeTime()
    versions = iter([1, 2, 1, 2])
    def predicate():
        version = next(versions)
        return version == 2
    assert wait_until(predicate, clock=fake.clock, sleep=fake.sleep) is True
    # A successful read does not prove that every replica has converged.


def test_snapshot_and_delta_idempotency_contract():
    events = [(1, 100), (2, 150), (1, 100)]
    latest = max(events, key=lambda x: x[0])
    assert latest == (2, 150)
    deltas = [(1, 100), (2, 50), (1, 100)]
    unique = dict(deltas)
    assert sum(unique.values()) == 150
