"""Real PostgreSQL -> ClickHouse reconciliation with raw MergeTree and VIEW.

The sink insertion is controlled by the tests. This verifies storage/read
semantics, not Kafka or asynchronous service delivery.
"""
from __future__ import annotations

from decimal import Decimal

import psycopg
import pytest

from data_qa.delivery_manifest import reconcile_delivery
from data_qa.delivery_quality import conflicting_versions, mismatched_event_payloads


def _event(event_id, trade_id, version, pnl, status="FILLED", account_id="A1"):
    return dict(event_id=event_id, trade_id=trade_id, account_id=account_id,
                version=version, pnl=Decimal(str(pnl)), status=status)


def _pg_write(dsn, events):
    with psycopg.connect(dsn) as conn:
        for event in events:
            conn.execute("""
                INSERT INTO lab07.trade_events
                (event_id, trade_id, account_id, version, pnl, status)
                VALUES (%(event_id)s, %(trade_id)s, %(account_id)s,
                        %(version)s, %(pnl)s, %(status)s)
            """, event)


def _pg_read(dsn, trade_id):
    with psycopg.connect(dsn) as conn:
        results = conn.execute("""
            SELECT event_id, trade_id, account_id, version, pnl, status
            FROM lab07.trade_events WHERE trade_id = %s
            ORDER BY row_id
        """, (trade_id,)).fetchall()
    return [
        _event(row[0], row[1], row[3], row[4], row[5], row[2])
        for row in results
    ]


def _ch_write(client, db, events):
    if events:
        client.execute(
            f"INSERT INTO {db}.trade_events_raw "
            "(event_id, trade_id, account_id, version, pnl, status) VALUES",
            [(e["event_id"], e["trade_id"], e["account_id"], e["version"],
              e["pnl"], e["status"]) for e in events],
        )


def _ch_read(client, db, trade_id):
    rows = client.execute(
        f"SELECT event_id, trade_id, account_id, version, pnl, status "
        f"FROM {db}.trade_events_raw WHERE trade_id = %(id)s",
        {"id": trade_id},
    )
    return [
        _event(row[0], row[1], row[3], row[4], row[5], row[2])
        for row in rows
    ]


def _latest(client, db, trade_id):
    return client.execute(
        f"SELECT version, pnl, status FROM {db}.trade_latest "
        "WHERE trade_id = %(id)s AND account_id = 'A1'",
        {"id": trade_id},
    )


def _report(source, target):
    return reconcile_delivery(
        [event["event_id"] for event in source],
        [event["event_id"] for event in target],
        planned_count=len(source),
    )


def test_latest_state_matches_even_when_history_missing(
    postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    db = ch_trade_tables
    events = [
        _event("E-1", trade_case_id, 1, "15.50"),
        _event("E-2", trade_case_id, 2, "20.00"),
    ]
    _pg_write(postgres_dsn, events)
    _ch_write(ch_client, db, [events[1]])
    source = _pg_read(postgres_dsn, trade_case_id)
    target = _ch_read(ch_client, db, trade_case_id)
    assert _latest(ch_client, db, trade_case_id) == [(2, Decimal("20.00"), "FILLED")]

    report = _report(source, target)
    assert report.missing == {"E-1"}
    assert report.unexpected == set()
    assert report.duplicates == {}
    assert not report.passed  # latest PASS must never hide missing history


def test_identical_duplicate_masks_missing_at_equal_total_count(
    postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    db = ch_trade_tables
    events = [
        _event("E-1", trade_case_id, 1, "15.50"),
        _event("E-2", trade_case_id, 2, "20.00"),
    ]
    _pg_write(postgres_dsn, events)
    _ch_write(ch_client, db, [events[1], events[1]])
    source = _pg_read(postgres_dsn, trade_case_id)
    target = _ch_read(ch_client, db, trade_case_id)

    assert len(source) == len(target) == 2
    report = _report(source, target)
    assert report.missing == {"E-1"}
    assert report.duplicates == {"E-2": 2}
    assert not report.passed


def test_same_version_conflict_is_not_ignored_by_latest_view(
    postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    db = ch_trade_tables
    original = _event("E-1", trade_case_id, 1, "15.50")
    conflict = _event("E-2", trade_case_id, 1, "18.00")
    _pg_write(postgres_dsn, [original])
    _ch_write(ch_client, db, [original, conflict])
    target = _ch_read(ch_client, db, trade_case_id)
    source = _pg_read(postgres_dsn, trade_case_id)

    assert _latest(ch_client, db, trade_case_id)  # not proof of quality
    assert conflicting_versions(target) == {
        (trade_case_id, "A1", 1): {
            (Decimal("15.50"), "FILLED"), (Decimal("18.00"), "FILLED")
        }
    }
    report = _report(source, target)
    assert report.unexpected == {"E-2"}
    assert not report.passed


def test_same_event_id_wrong_pnl_is_separate_payload_mismatch(
    postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    db = ch_trade_tables
    source_event = _event("E-1", trade_case_id, 1, "15.50")
    corrupted = _event("E-1", trade_case_id, 1, "17.00")
    _pg_write(postgres_dsn, [source_event])
    _ch_write(ch_client, db, [corrupted])
    source = _pg_read(postgres_dsn, trade_case_id)
    target = _ch_read(ch_client, db, trade_case_id)

    assert _report(source, target).passed  # IDs alone are insufficient
    assert set(mismatched_event_payloads(source, target)) == {"E-1"}


def test_complete_history_and_latest_state(
    postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    db = ch_trade_tables
    events = [
        _event("E-1", trade_case_id, 1, "15.50"),
        _event("E-2", trade_case_id, 2, "20.00"),
    ]
    _pg_write(postgres_dsn, events)
    _ch_write(ch_client, db, events)
    source = _pg_read(postgres_dsn, trade_case_id)
    target = _ch_read(ch_client, db, trade_case_id)

    assert _report(source, target).passed
    assert mismatched_event_payloads(source, target) == {}
    assert conflicting_versions(target) == {}
    assert _latest(ch_client, db, trade_case_id) == [(2, Decimal("20.00"), "FILLED")]


def test_empty_target_is_not_valid_when_source_expected(
    postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    event = _event("E-1", trade_case_id, 1, "15.50")
    _pg_write(postgres_dsn, [event])
    source = _pg_read(postgres_dsn, trade_case_id)
    assert len(source) == 1
    report = _report(source, _ch_read(ch_client, ch_trade_tables, trade_case_id))
    assert report.missing == {"E-1"}
    assert not report.passed
