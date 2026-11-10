"""Session 07 learner exercise: PostgreSQL READ COMMITTED and explicit rollback."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import psycopg


def count_trades(conn: psycopg.Connection, trade_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM lab07.trades WHERE trade_id = %s",
        (trade_id,),
    ).fetchone()
    assert row is not None
    return row[0]


def test_uncommitted_trade_invisible_and_rollback(postgres_dsn: str) -> None:
    """An INSERT is visible to its transaction, not to a second connection."""
    trade_id = f"T-{uuid4().hex}"

    with psycopg.connect(postgres_dsn) as conn_a:
        with psycopg.connect(postgres_dsn) as conn_b:
            # 1. A inserts a unique trade, without committing.
            conn_a.execute(
                "INSERT INTO lab07.trades (trade_id, pnl) VALUES (%s, %s)",
                (trade_id, Decimal("15.50")),
            )

            # 2. A sees its own uncommitted write.
            assert count_trades(conn_a, trade_id) == 1

            # 3. B must not see another connection's uncommitted write.
            assert count_trades(conn_b, trade_id) == 0

            # 4. A discards the INSERT.
            conn_a.rollback()

            # 5. Neither A nor B can see the rolled-back record.
            assert count_trades(conn_a, trade_id) == 0
            assert count_trades(conn_b, trade_id) == 0
