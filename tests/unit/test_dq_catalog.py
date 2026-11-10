"""Contract-level tests for independent DQ rules and no-vacuous-PASS behavior."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "exercises/06-data-quality-rules/starter/rule_runner.py"
FIXTURE = ROOT / "exercises/06-data-quality-rules/fixtures/dq_batches.json"
AS_OF = "2026-11-08T13:00:00Z"
EVENT = "2026-11-08T12:00:00Z"
ON_TIME = "2026-11-08T12:01:00Z"
LATE = "2026-11-08T12:20:00Z"


def make_event(event_id: str, *, trade_id: str | None = None, version: int = 1,
               pnl: str | None = "0.00", status: str = "FILLED",
               available_at: str | None = ON_TIME) -> dict:
    return {
        "event_id": event_id, "trade_id": trade_id or event_id,
        "account_id": "A1", "version": version, "status": status,
        "pnl": pnl, "event_time": EVENT, "available_at": available_at,
    }


def report_for(tmp_path: Path, records: list[dict], *, expected_events: int | None = None,
               **extra) -> dict:
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "cohorts": [{
            "name": "test", "as_of": AS_OF,
            "expected_events": len(records) if expected_events is None else expected_events,
            "records": records, **extra,
        }],
    }), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(RUNNER), str(path), "--format", "json"],
                          text=True, capture_output=True, cwd=ROOT, timeout=10)
    assert proc.returncode in (0, 1), proc.stderr
    result = json.loads(proc.stdout)["cohorts"][0]
    return result


def rule(report: dict, number: int) -> dict:
    match = [r for r in report["results"] if r["rule_id"] == f"DQ-{number:02}"]
    assert len(match) == 1
    return match[0]


def test_bundled_mixed_anomalies_detect_independent_rules() -> None:
    process = subprocess.run([sys.executable, str(RUNNER), str(FIXTURE),
                             "--cohort", "mixed_anomalies", "--format", "json"],
                             text=True, capture_output=True, cwd=ROOT, timeout=10)
    assert process.returncode == 1, process.stderr
    report = json.loads(process.stdout)["cohorts"][0]
    assert len(report["results"]) == 20
    for number in (1, 2, 4, 5, 6, 9, 11):
        assert rule(report, number)["status"] == "FAIL"
    for number in (3, 7, 12, 13, 16):
        assert rule(report, number)["status"] == "PASS"
    for number in (8, 10, 14, 15, 17, 18, 19, 20):
        assert rule(report, number)["status"] == "INDETERMINATE"
    assert rule(report, 9)["issues"][0]["trade_id"] == "T-13"
    assert rule(report, 11)["issues"][0]["event_id"] == "E-103"


def test_one_event_id_conflict_stays_separate_from_redelivery(tmp_path: Path) -> None:
    first = make_event("E1")
    changed = {**first, "pnl": "2.00"}
    outcome = report_for(tmp_path, [first, changed], expected_events=1)
    assert rule(outcome, 2)["status"] == "INDETERMINATE"
    assert rule(outcome, 3)["status"] == "FAIL"
    assert rule(outcome, 9)["status"] == "PASS"


def test_same_version_two_event_ids_conflicting_pnl(tmp_path: Path) -> None:
    first = make_event("E1", trade_id="T1", pnl="7.00")
    second = make_event("E2", trade_id="T1", pnl="8.00")
    outcome = report_for(tmp_path, [first, second])
    assert rule(outcome, 2)["status"] == "PASS"
    assert rule(outcome, 3)["status"] == "PASS"
    assert rule(outcome, 9)["status"] == "FAIL"


def test_same_version_equal_decimal_values_not_conflicting(tmp_path: Path) -> None:
    first = make_event("E1", trade_id="T1", pnl="7.00")
    second = make_event("E2", trade_id="T1", pnl="7.0")
    outcome = report_for(tmp_path, [first, second])
    assert rule(outcome, 9)["status"] == "PASS"


def test_business_consistency_nullable_pnl_by_status(tmp_path: Path) -> None:
    records = [make_event("E1", status="NEW", pnl=None),
               make_event("E2", status="FILLED", pnl=None)]
    outcome = report_for(tmp_path, records)
    assert rule(outcome, 6)["status"] == "PASS"  # NULL is not malformed Decimal
    assert rule(outcome, 13)["status"] == "FAIL"
    assert rule(outcome, 13)["issues"][0]["event_id"] == "E2"


def test_blank_id_and_invalid_version_are_separate(tmp_path: Path) -> None:
    row = make_event("E1", version=0)
    row["trade_id"] = ""
    outcome = report_for(tmp_path, [row], expected_events=1)
    assert rule(outcome, 1)["status"] == "PASS"  # presence alone
    assert rule(outcome, 4)["status"] == "FAIL"
    assert rule(outcome, 16)["status"] == "FAIL"


def test_missing_expected_identity_even_when_cardinality_matches(tmp_path: Path) -> None:
    outcome = report_for(tmp_path, [make_event("E1")], expected_events=1,
                         expected_event_ids=["E999"])
    assert rule(outcome, 7)["status"] == "FAIL"
    assert rule(outcome, 7)["metrics"]["observed_distinct_count"] == 1


@pytest.mark.parametrize("on_time,late,unknown,expected_status", [
    (96, 4, 0, "PASS"),
    (94, 6, 0, "FAIL"),
    (94, 4, 2, "INDETERMINATE"),
    (95, 4, 1, "PASS"),
])
def test_95_percent_sla_bounds(tmp_path: Path, on_time: int, late: int,
                                unknown: int, expected_status: str) -> None:
    times = [ON_TIME] * on_time + [LATE] * late + [None] * unknown
    records = [make_event(f"E-{i}", available_at=t) for i, t in enumerate(times)]
    manifest = [{"event_id": r["event_id"], "event_time": EVENT} for r in records]
    outcome = report_for(tmp_path, records, expected_events=100,
                         expected_event_manifest=manifest)
    assert rule(outcome, 8)["status"] == expected_status
    assert rule(outcome, 8)["metrics"]["eligible_count"] == 100
    assert rule(outcome, 8)["metrics"]["unknown_count"] == unknown
    if late:
        assert rule(outcome, 11)["status"] == "FAIL"


def test_unseen_matured_source_event_is_overdue(tmp_path: Path) -> None:
    outcome = report_for(tmp_path, [make_event("E1")], expected_events=2,
                         expected_event_manifest=[
                             {"event_id": "E1", "event_time": EVENT},
                             {"event_id": "E2", "event_time": EVENT},
                         ])
    assert rule(outcome, 7)["status"] == "FAIL"
    assert rule(outcome, 8)["status"] == "FAIL"
    assert rule(outcome, 8)["metrics"]["overdue_unobserved_count"] == 1


def test_no_matured_events_not_sla_pass(tmp_path: Path) -> None:
    recent = "2026-11-08T12:59:00Z"
    row = {**make_event("E1"), "event_time": recent}
    outcome = report_for(tmp_path, [row], expected_events=1,
                         expected_event_manifest=[{"event_id": "E1", "event_time": recent}])
    assert rule(outcome, 8)["status"] == "INDETERMINATE"
    assert rule(outcome, 8)["metrics"]["eligible_count"] == 0


def test_source_target_categories_are_not_cross_mixed(tmp_path: Path) -> None:
    s1 = make_event("SRC1", trade_id="T1", status="FILLED", pnl="12.00")
    t1 = make_event("DST1", trade_id="T1", status="FAILED", pnl="10.00")
    orphan = make_event("DST2", trade_id="T2")
    failing = make_event("DST3", trade_id="T3", status="FAILED")
    unknown = make_event("DST4", trade_id="T4", status="UNSUPPORTED")
    outcome = report_for(tmp_path, [make_event("E0")], expected_events=1,
                         source_records=[s1],
                         target_records=[t1, orphan, failing, unknown],
                         reconciliation_finalized=True, target_grain="snapshot")
    assert rule(outcome, 10)["status"] == "FAIL"
    assert rule(outcome, 14)["status"] == "FAIL"
    assert {i["reason"] for i in rule(outcome, 14)["issues"]} == {"ORPHAN"}
    assert rule(outcome, 17)["status"] == "PASS"
    assert rule(outcome, 18)["status"] == "FAIL"
    assert rule(outcome, 19)["status"] == "FAIL"
    assert rule(outcome, 20)["status"] == "FAIL"


def test_target_cardinality_and_missing_orphan_use_composite_key(tmp_path: Path) -> None:
    source = [make_event("S1", trade_id="T1")]
    target = [make_event("R1", trade_id="T1"),
              make_event("R2", trade_id="T1"),
              {**make_event("R3", trade_id="T1"), "account_id": "A2"}]
    outcome = report_for(tmp_path, [make_event("E0")],
                         source_records=source, target_records=target,
                         reconciliation_finalized=True, target_grain="snapshot")
    duplicates = rule(outcome, 15)
    assert duplicates["status"] == "FAIL"
    assert duplicates["issues"][0]["processing_count"] == 2
    orphans = rule(outcome, 14)["issues"]
    assert len(orphans) == 1 and orphans[0]["account_id"] == "A2"


def test_source_target_version_lag_is_not_status_or_pnl_conflict(tmp_path: Path) -> None:
    source = [make_event("S1", trade_id="T1", version=2)]
    target = [make_event("R1", trade_id="T1", version=1)]
    outcome = report_for(tmp_path, [make_event("E0")],
                         source_records=source, target_records=target,
                         reconciliation_finalized=True)
    assert rule(outcome, 17)["status"] == "FAIL"
    assert rule(outcome, 10)["status"] == "INDETERMINATE"
    assert rule(outcome, 20)["status"] == "INDETERMINATE"
