"""DQ-02 integration cases: replay identity, uncertainty and stable gate semantics."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "exercises/06-data-quality-rules/starter/rule_runner.py"


def evaluate(tmp_path: Path, records: list[dict], expected_events: int = 2) -> tuple[int, dict]:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "schema_version": 1,
        "cohorts": [{"name": "case", "expected_events": expected_events, "records": records}],
    }), encoding="utf-8")
    process = subprocess.run(
        [sys.executable, str(RUNNER), str(fixture), "--format", "json"],
        text=True, capture_output=True, timeout=10, check=False, cwd=ROOT,
    )
    assert process.returncode in (0, 1), process.stderr
    return process.returncode, json.loads(process.stdout)["cohorts"][0]


def test_new_trade_version_is_not_a_duplicate(tmp_path: Path) -> None:
    rows = [
        {"event_id": "E1", "trade_id": "T1", "account_id": "A1", "version": 1, "status": "NEW"},
        {"event_id": "E2", "trade_id": "T1", "account_id": "A1", "version": 2, "status": "FILLED"},
    ]
    code, report = evaluate(tmp_path, rows)
    assert code == 1  # upstream SLA/source data not provided
    assert [r["status"] for r in report["results"][:2]] == ["PASS", "PASS"]


def test_replay_n_minus_one_and_metadata_is_not_payload(tmp_path: Path) -> None:
    event = {"event_id": "E1", "trade_id": "T1", "account_id": "A1",
             "version": 1, "status": "NEW", "available_at": "2026-11-09T10:00:00Z"}
    rows = [event, dict(event), {**event, "available_at": "2026-11-09T10:01:00Z"}]
    code, report = evaluate(tmp_path, rows, expected_events=1)
    assert code == 1  # warning does not fail gate; missing manifest is INDETERMINATE
    assert report["results"][1]["status"] == "FAIL"
    issue = report["results"][1]["issues"][0]
    assert issue["duplicate_count"] == 2 and issue["delivery_count"] == 3
    assert report["overall_status"] == "INDETERMINATE"


def test_conflicting_payload_needs_separate_dq03(tmp_path: Path) -> None:
    original = {"event_id": "E1", "trade_id": "T1", "account_id": "A1",
                "version": 2, "status": "FILLED", "pnl": "7.00"}
    code, report = evaluate(tmp_path, [original, {**original, "pnl": "8.00"}], expected_events=1)
    assert code == 1
    assert report["results"][1]["status"] == "INDETERMINATE"
    assert report["results"][1]["issues"][0]["reason"] == "same_event_id_requires_DQ-03"
    assert report["results"][2]["status"] == "FAIL"
    assert report["results"][2]["issues"][0]["reason"] == "immutable_event_payload_conflict"


def test_missing_identity_is_not_an_empty_pass(tmp_path: Path) -> None:
    rows = [{"trade_id": "T1", "account_id": "A1", "version": 1, "status": "NEW"}]
    code, report = evaluate(tmp_path, rows)
    assert code == 1
    assert report["results"][0]["status"] == "FAIL"
    assert report["results"][1]["status"] == "INDETERMINATE"
