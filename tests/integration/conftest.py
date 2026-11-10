"""Real PostgreSQL lifecycle for Session 07 (requires Docker + Testcontainers).

This fixture starts a fresh database per pytest worker process, applies the
schema once, then removes the container at the end of that worker's session.
It does NOT manage the lifecycle of an external API or ClickHouse.
"""

from __future__ import annotations

from collections.abc import Iterator

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
        # Context manager commits DDL before any tests receive the DSN.
        yield dsn
        # Testcontainers' context manager tears down the container,
        # including when a test assertion fails.
