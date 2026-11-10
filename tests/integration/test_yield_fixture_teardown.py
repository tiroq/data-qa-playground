"""Prove real Psycopg teardown semantics even when a pytest assertion fails.

A nested pytest subprocess deliberately has two RED tests. The *outer* test
passes only if their finalizers leave the database in the expected state.
"""
from __future__ import annotations

from uuid import uuid4

import psycopg
import pytest

pytest_plugins = ("pytester",)


def test_rollback_fixture_vs_context_manager_after_failing_assertion(
    pytester: pytest.Pytester,
    postgres_dsn: str,
) -> None:
    rollback_key = f"rollback-{uuid4().hex}"
    autocommit_key = f"committed-{uuid4().hex}"

    pytester.makepyfile(
        test_failure=f"""
import pytest
import psycopg

DSN = {postgres_dsn!r}
ROLLBACK_KEY = {rollback_key!r}
AUTO_COMMIT_KEY = {autocommit_key!r}

@pytest.fixture
def transaction_rollback():
    conn = psycopg.connect(DSN)
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()

@pytest.fixture
def connection_context():
    with psycopg.connect(DSN) as conn:
        yield conn

def test_failing_assertion_still_rolls_back(transaction_rollback):
    transaction_rollback.execute(
        "INSERT INTO lab07.trades (trade_id, pnl) VALUES (%s, 15.50)",
        (ROLLBACK_KEY,),
    )
    assert False, "Intentional failure: verify rollback teardown"

def test_failing_assertion_still_commits_with_context(connection_context):
    connection_context.execute(
        "INSERT INTO lab07.trades (trade_id, pnl) VALUES (%s, 15.50)",
        (AUTO_COMMIT_KEY,),
    )
    assert False, "Intentional failure: WITH context commits on generator resume"
"""
    )

    try:
        nested = pytester.runpytest_subprocess("-q")
        nested.assert_outcomes(failed=2)
        with psycopg.connect(postgres_dsn) as conn:
            rows = conn.execute(
                "SELECT trade_id FROM lab07.trades WHERE trade_id IN (%s, %s)",
                (rollback_key, autocommit_key),
            ).fetchall()
        assert set(rows) == {(autocommit_key,)}
    finally:
        # Cleanup of the deliberately committed row even if the outer assert fails.
        with psycopg.connect(postgres_dsn) as conn:
            conn.execute(
                "DELETE FROM lab07.trades WHERE trade_id IN (%s, %s)",
                (rollback_key, autocommit_key),
            )
