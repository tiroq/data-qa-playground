"""Real local HTTP 202 -> background worker -> PostgreSQL -> ClickHouse.

The transport is HTTP on localhost and databases run in Testcontainers.
This synthetic service intentionally does not claim to implement real Kafka.
"""
from __future__ import annotations

import time
from decimal import Decimal
from urllib.error import HTTPError

import psycopg
import pytest

from data_qa.delivery_manifest import reconcile_delivery
from data_qa.delivery_quality import mismatched_event_payloads
from lab_api import LabAPI


@pytest.fixture
def lab_api(postgres_dsn, clickhouse_dsn, ch_trade_tables, trade_case_id):
    # Dependency on trade_case_id ensures server stops before PG cleanup.
    with LabAPI(postgres_dsn, clickhouse_dsn, ch_trade_tables) as service:
        yield service


def payload(trade_id, version=1, event_id=None, fault=None, pnl="15.50"):
    data = {
        "trade_id": trade_id,
        "account_id": "A1",
        "version": version,
        "pnl": pnl,
        "status": "FILLED",
    }
    if event_id is not None:
        data["event_id"] = event_id
    if fault is not None:
        data["_lab_fault"] = fault
    return data


def _read_pg(dsn, trade_id):
    with psycopg.connect(dsn) as conn:
        rows = conn.execute(
            "SELECT event_id, trade_id, account_id, version, pnl, status "
            "FROM lab07.trade_events WHERE trade_id = %s ORDER BY row_id",
            (trade_id,),
        ).fetchall()
    return [
        dict(event_id=r[0], trade_id=r[1], account_id=r[2],
             version=r[3], pnl=r[4], status=r[5])
        for r in rows
    ]


def _read_ch(client, db, trade_id):
    rows = client.execute(
        f"SELECT event_id, trade_id, account_id, version, pnl, status "
        f"FROM {db}.trade_events_raw WHERE trade_id = %(id)s",
        {"id": trade_id},
    )
    return [
        dict(event_id=r[0], trade_id=r[1], account_id=r[2],
             version=r[3], pnl=r[4], status=r[5])
        for r in rows
    ]


def _poll_pg(dsn, trade_id, *, timeout=5.0, interval=0.05):
    """Session 07 fixture-local bounded polling, not Session 08's assignment."""
    deadline = time.monotonic() + timeout
    last = []
    while True:
        last = _read_pg(dsn, trade_id)
        if last:
            return last
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"PostgreSQL arrival timeout: {trade_id}; last={last}")
        time.sleep(min(interval, remaining))


def test_http_202_precedes_persistence_then_final_state_passes(
    lab_api, postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    lab_api.pause_worker()
    try:
        http_status, response = lab_api.post(payload(trade_case_id))
        assert http_status == 202
        assert response["trade_id"] == trade_case_id
        assert response["event_id"].startswith("E-")
        # Deterministic gate: an accepted event is not yet committed in PG.
        assert _read_pg(postgres_dsn, trade_case_id) == []
    finally:
        lab_api.resume_worker()

    source = _poll_pg(postgres_dsn, trade_case_id)
    outcomes = lab_api.wait_completed([response["event_id"]])
    assert outcomes == {response["event_id"]: "stored"}
    target = _read_ch(ch_client, ch_trade_tables, trade_case_id)
    assert reconcile_delivery(
        [e["event_id"] for e in source],
        [e["event_id"] for e in target],
        planned_count=1,
    ).passed
    assert mismatched_event_payloads(source, target) == {}
    latest = ch_client.execute(
        f"SELECT version, pnl, status FROM {ch_trade_tables}.trade_latest "
        "WHERE trade_id = %(id)s",
        {"id": trade_case_id},
    )
    assert latest == [(1, Decimal("15.50"), "FILLED")]


def test_after_completion_dropped_sink_event_is_missing(
    lab_api, postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    status, response = lab_api.post(payload(trade_case_id, fault="skip_sink"))
    assert status == 202
    assert lab_api.wait_completed([response["event_id"]]) == {
        response["event_id"]: "skipped"
    }
    source = _read_pg(postgres_dsn, trade_case_id)
    target = _read_ch(ch_client, ch_trade_tables, trade_case_id)
    assert len(source) == 1 and target == []
    report = reconcile_delivery(
        [row["event_id"] for row in source],
        [row["event_id"] for row in target],
        planned_count=1,
    )
    assert report.missing == {response["event_id"]}
    assert not report.passed


def test_after_completion_duplicate_masks_missing(
    lab_api, postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    status1, r1 = lab_api.post(
        payload(trade_case_id, version=1, event_id="E-first", fault="skip_sink")
    )
    status2, r2 = lab_api.post(
        payload(trade_case_id, version=2, event_id="E-second",
                fault="duplicate_sink", pnl="20.00")
    )
    assert (status1, status2) == (202, 202)
    assert lab_api.wait_completed([r1["event_id"], r2["event_id"]]) == {
        "E-first": "skipped", "E-second": "stored"
    }
    source = _read_pg(postgres_dsn, trade_case_id)
    target = _read_ch(ch_client, ch_trade_tables, trade_case_id)
    assert len(source) == len(target) == 2
    report = reconcile_delivery(
        [row["event_id"] for row in source],
        [row["event_id"] for row in target],
        planned_count=2,
    )
    assert report.missing == {"E-first"}
    assert report.duplicates == {"E-second": 2}
    assert not report.passed


def test_after_completion_corrupted_pnl_fails_payload_check(
    lab_api, postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    _, response = lab_api.post(payload(trade_case_id, fault="corrupt_sink"))
    assert lab_api.wait_completed([response["event_id"]]) == {
        response["event_id"]: "stored"
    }
    source = _read_pg(postgres_dsn, trade_case_id)
    target = _read_ch(ch_client, ch_trade_tables, trade_case_id)
    assert reconcile_delivery(
        [e["event_id"] for e in source],
        [e["event_id"] for e in target],
        planned_count=1,
    ).passed
    assert set(mismatched_event_payloads(source, target)) == {response["event_id"]}


def test_invalid_api_request_is_rejected_without_records(
    lab_api, postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    with pytest.raises(HTTPError) as error:
        lab_api.post({"trade_id": trade_case_id})
    assert error.value.code == 400
    assert _read_pg(postgres_dsn, trade_case_id) == []
    assert _read_ch(ch_client, ch_trade_tables, trade_case_id) == []


def test_processing_barrier_times_out_when_worker_is_paused(
    lab_api, postgres_dsn, trade_case_id, ch_client, ch_trade_tables
):
    """No false PASS when HTTP accepts a trade but processing is still in-flight."""
    lab_api.pause_worker()
    try:
        status, response = lab_api.post(payload(trade_case_id))
        assert status == 202
        with pytest.raises(TimeoutError, match="pending"):
            lab_api.wait_completed([response["event_id"]], timeout=0.05)
        assert _read_pg(postgres_dsn, trade_case_id) == []
        assert _read_ch(ch_client, ch_trade_tables, trade_case_id) == []
    finally:
        lab_api.resume_worker()
    assert lab_api.wait_completed([response["event_id"]]) == {
        response["event_id"]: "stored"
    }


def test_bounded_source_poll_timeout_has_diagnostics(postgres_dsn, trade_case_id):
    """A missing source event must not yield a vacuous success or loop forever."""
    with pytest.raises(TimeoutError, match=trade_case_id):
        _poll_pg(postgres_dsn, trade_case_id, timeout=0.03, interval=0.01)
