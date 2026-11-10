"""Real PostgreSQL lifecycle for Session 07 (requires Docker + Testcontainers).

This fixture starts a fresh database per pytest worker process, applies the
schema once, then removes the container at the end of that worker's session.
It does NOT manage the lifecycle of an external API or ClickHouse.
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_dsn() -> Iterator[str]:
    """One isolated PostgreSQL container and committed lab schema per worker."""
    with PostgresContainer("postgres:16-alpine", driver=None) as postgres:
        dsn = postgres.get_connection_url()
        with psycopg.connect(dsn) as admin:
            admin.execute("CREATE SCHEMA lab07")
            admin.execute(
                """
                CREATE TABLE lab07.trades (
                    trade_id TEXT PRIMARY KEY,
                    pnl NUMERIC(18, 2) NOT NULL
                )
                """
            )
            # Physical event rows, not deduplicated logical trade states:
            admin.execute(
                """
                CREATE TABLE lab07.trade_events (
                    row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    trade_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    pnl NUMERIC(18, 2),
                    status TEXT
                )
                """
            )
        # DDL is committed before the DSN is passed to tests.
        yield dsn
        # The Testcontainers context manager tears down the database.


@pytest.fixture(scope="function")
def trade_case_id(postgres_dsn: str) -> Iterator[str]:
    """Unique per-test business key and cleanup, including assertion failures.

    This is safe for *synchronous* committed writes by the test. It does not
    prevent late asynchronous writes from an external API/queue.
    """
    trade_id = f"T-{uuid4().hex}"
    try:
        yield trade_id
    finally:
        with psycopg.connect(postgres_dsn) as conn:
            conn.execute(
                "DELETE FROM lab07.trade_events WHERE trade_id = %s",
                (trade_id,),
            )
