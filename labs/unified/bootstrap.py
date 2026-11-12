"""Prepare only isolated streaming_lab schemas; safe to run repeatedly."""
from __future__ import annotations

from pathlib import Path

import psycopg

from common import PG_DSN, clickhouse_query

ROOT = Path(__file__).resolve().parent


def statements(path: Path) -> list[str]:
    # Scripts contain only simple DDL, no semicolons in string literals.
    text = "\n".join(line for line in path.read_text().splitlines()
                     if not line.lstrip().startswith("--"))
    return [statement.strip() for statement in text.split(";") if statement.strip()]


def main() -> None:
    with psycopg.connect(PG_DSN) as connection:
        for sql in statements(ROOT / "sql/postgres.sql"):
            connection.execute(sql)
    for sql in statements(ROOT / "sql/clickhouse.sql"):
        clickhouse_query(sql)
    print("STREAMING_BOOTSTRAP_READY: PostgreSQL and ClickHouse streaming_lab created")


if __name__ == "__main__":
    main()
