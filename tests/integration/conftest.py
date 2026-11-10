"""Isolated PostgreSQL / ClickHouse Testcontainers for Session 07.

A container lives for one pytest worker session; business data/ClickHouse
database lives for one test. No production API, Kafka or shared databases.
"""
from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_dsn() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine", driver=None) as postgres:
        dsn = postgres.get_connection_url()
        with psycopg.connect(dsn) as admin:
            admin.execute("CREATE SCHEMA lab07")
            admin.execute("""
                CREATE TABLE lab07.trades (
                    trade_id TEXT PRIMARY KEY,
                    pnl NUMERIC(18, 2) NOT NULL
                )
            """)
            admin.execute("""
                CREATE TABLE lab07.trade_events (
                    row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    trade_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    pnl NUMERIC(18, 2),
                    status TEXT,
                    event_id TEXT
                )
            """)
        yield dsn


@pytest.fixture(scope="function")
def trade_case_id(postgres_dsn: str) -> Iterator[str]:
    """Cleanup happens even after assertions fail, but not after process kill."""
    trade_id = f"T-{uuid4().hex}"
    try:
        yield trade_id
    finally:
        with psycopg.connect(postgres_dsn) as conn:
            conn.execute(
                "DELETE FROM lab07.trade_events WHERE trade_id = %s",
                (trade_id,),
            )


@pytest.fixture(scope="session")
def clickhouse_dsn() -> Iterator[str]:
    """One ClickHouse container per pytest worker, never shared between workers."""
    from testcontainers.clickhouse import ClickHouseContainer

    with ClickHouseContainer("clickhouse/clickhouse-server:25.8") as clickhouse:
        yield clickhouse.get_connection_url()


@pytest.fixture(scope="function")
def ch_client(clickhouse_dsn: str):
    """A ClickHouse native driver client belongs to exactly one thread."""
    from clickhouse_driver import Client

    client = Client.from_url(clickhouse_dsn)
    try:
        assert client.execute("SELECT 1") == [(1,)]
        yield client
    finally:
        client.disconnect()


@pytest.fixture(scope="function")
def ch_case_db(ch_client) -> Iterator[str]:
    """Database per test prevents residue without asynchronous mutations."""
    db = f"qa_{uuid4().hex}"
    ch_client.execute(f"CREATE DATABASE {db}")
    try:
        yield db
    finally:
        ch_client.execute(f"DROP DATABASE IF EXISTS {db} SYNC")


@pytest.fixture(scope="function")
def ch_trade_tables(ch_client, ch_case_db: str) -> str:
    """Raw physical history + query-time latest projection."""
    db = ch_case_db
    ch_client.execute(f"""
        CREATE TABLE {db}.trade_events_raw (
            event_id String,
            trade_id String,
            account_id String,
            version UInt32,
            pnl Decimal(18, 2),
            status String
        )
        ENGINE = MergeTree
        ORDER BY (trade_id, account_id, version, event_id)
    """)
    ch_client.execute(f"""
        CREATE VIEW {db}.trade_latest AS
        SELECT
            trade_id,
            account_id,
            latest_version AS version,
            tupleElement(latest_payload, 1) AS pnl,
            tupleElement(latest_payload, 2) AS status
        FROM (
            SELECT
                trade_id,
                account_id,
                max(version) AS latest_version,
                argMax(tuple(pnl, status), version) AS latest_payload
            FROM {db}.trade_events_raw
            GROUP BY trade_id, account_id
        )
    """)
    return db
