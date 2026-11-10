"""Real PostgreSQL contract checks for committed writes, not HTTP API E2E.

A separate PostgreSQL connection simulates an API process that commits its own
transaction. No real API, transport, or ClickHouse is started in this suite.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal

import psycopg
import pytest


@dataclass(frozen=True)
class Snapshot:
    total: int
    matching: int
    conflicting: int


def observe(
    conn: psycopg.Connection,
    *,
    trade_id: str,
    account_id: str,
    version: int,
    pnl: Decimal,
    status: str,
) -> Snapshot:
    """One SQL statement = one READ COMMITTED snapshot, not three races."""
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (
                WHERE pnl = %s AND status = %s
            ) AS matching,
            COUNT(*) FILTER (
                WHERE pnl IS DISTINCT FROM %s
                   OR status IS DISTINCT FROM %s
            ) AS conflicting
        FROM lab07.trade_events
        WHERE trade_id = %s AND account_id = %s AND version = %s
        """,
        (pnl, status, pnl, status, trade_id, account_id, version),
    ).fetchone()
    assert row is not None
    return Snapshot(*row)


def wait_for_observation(
    conn: psycopg.Connection,
    *,
    timeout: float,
    interval: float = 0.2,
    **identity_and_payload,
) -> Snapshot:
    """Wait only for presence. Payload/duplicate correctness is checked next."""
    if timeout < 0 or interval <= 0:
        raise ValueError("timeout must be nonnegative and interval must be positive")
    deadline = time.monotonic() + timeout
    while True:
        observation = observe(conn, **identity_and_payload)
        if observation.total:
            return observation
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                f"Trade was never observed before timeout: {identity_and_payload}"
            )
        time.sleep(min(interval, remaining))


def check_contract(snapshot: Snapshot) -> list[str]:
    """Report independent contract violations without stopping at first defect."""
    failures = []
    if snapshot.total != 1:
        failures.append(f"physical row count={snapshot.total}, expected=1")
    if snapshot.matching != 1:
        failures.append(f"matching payload count={snapshot.matching}, expected=1")
    if snapshot.conflicting != 0:
        failures.append(f"conflicting payload count={snapshot.conflicting}, expected=0")
    return failures


@pytest.mark.parametrize(
    ("records", "expected_issues"),
    [
        ([("15.50", "FILLED")], 0),
        ([("15.50", "FILLED"), ("15.50", "FILLED")], 2),
        ([("15.50", "FILLED"), ("16.00", "FILLED")], 2),
        ([("16.00", "FILLED")], 2),
    ],
    ids=["healthy", "identical-duplicate", "same-version-conflict", "wrong-pnl"],
)
def test_committed_writer_data_contract(
    postgres_dsn: str,
    trade_case_id: str,
    records: list[tuple[str, str]],
    expected_issues: int,
) -> None:
    """Committed writes are read from an independent connection."""
    account_id, version = "A1", 1
    with psycopg.connect(postgres_dsn) as writer:
        for pnl, status in records:
            writer.execute(
                """
                INSERT INTO lab07.trade_events (
                    trade_id, account_id, version, pnl, status
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (trade_case_id, account_id, version, Decimal(pnl), status),
            )
    # Writer exits its context and COMMITs before the observer queries data.
    with psycopg.connect(postgres_dsn) as reader:
        snapshot = wait_for_observation(
            reader,
            timeout=1.0,
            trade_id=trade_case_id,
            account_id=account_id,
            version=version,
            pnl=Decimal("15.50"),
            status="FILLED",
        )
    problems = check_contract(snapshot)
    assert len(problems) == expected_issues, (
        f"Unexpected diagnostics for {snapshot}: {problems}"
    )
    if expected_issues == 0:
        assert not problems, "\n".join(problems)


def test_missing_committed_trade_never_passes(
    postgres_dsn: str,
    trade_case_id: str,
) -> None:
    """A missing record is a timeout, not a vacuously successful equality."""
    with psycopg.connect(postgres_dsn) as reader:
        with pytest.raises(TimeoutError, match="never observed"):
            wait_for_observation(
                reader,
                timeout=0.03,
                interval=0.01,
                trade_id=trade_case_id,
                account_id="A1",
                version=1,
                pnl=Decimal("15.50"),
                status="FILLED",
            )
