"""Integration tests for the Session 06 runner and the current DQ-01 rule."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "exercises/06-data-quality-rules/starter/rule_runner.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), "--format", "json", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_all_cohorts_have_an_explicit_report() -> None:
    completed = run_cli()
    assert completed.returncode == 1, completed.stderr
    report = json.loads(completed.stdout)
    assert report["summary"] == {
        "overall_status": "FAIL",
        "cohorts": 3,
        "pass": 0,
        "fail": 2,
        "indeterminate": 1,
        "implemented_rules": [f"DQ-{i:02}" for i in range(1, 21)],
    }
    by_name = {row["cohort"]: row for row in report["cohorts"]}
    assert by_name["mostly_healthy"]["results"][0]["status"] == "PASS"
    mixed_rule = by_name["mixed_anomalies"]["results"][0]
    assert mixed_rule["status"] == "FAIL"
    assert mixed_rule["issues"][0]["event_id"] == "E-104"
    assert mixed_rule["issues"][0]["field"] == "trade_id"
    replay = by_name["mixed_anomalies"]["results"][1]
    assert replay["status"] == "FAIL"
    assert replay["severity"] == "warning"
    assert replay["issues"][0]["event_id"] == "E-102"
    assert replay["issues"][0]["duplicate_count"] == 1
    empty = by_name["empty_input"]
    assert empty["input_gate"]["status"] == "FAIL"
    assert empty["results"][0]["status"] == "INDETERMINATE"
    assert empty["results"][1]["status"] == "INDETERMINATE"
    assert empty["overall_status"] == "FAIL"


def test_healthy_cohort_exits_successfully() -> None:
    completed = run_cli("--cohort", "mostly_healthy")
    assert completed.returncode == 1, completed.stderr
    row = json.loads(completed.stdout)["cohorts"][0]
    assert row["overall_status"] == "INDETERMINATE"
    assert row["coverage_status"] == "PARTIAL"
    assert row["results"][0]["status"] == "PASS"
    assert row["results"][1]["status"] == "PASS"
    assert row["results"][7]["rule_id"] == "DQ-08"
    assert row["results"][7]["status"] == "INDETERMINATE"
    assert row["results"][7]["issues"][0]["reason"] == "missing_source_event_manifest"


def test_json_output_can_be_saved(tmp_path: Path) -> None:
    output = tmp_path / "reports" / "dq.json"
    completed = run_cli("--cohort", "mixed_anomalies", "--output", str(output))
    assert completed.returncode == 1, completed.stderr
    assert json.loads(output.read_text(encoding="utf-8")) == json.loads(completed.stdout)


def test_unknown_cohort_does_not_silently_pass() -> None:
    completed = run_cli("--cohort", "not-a-cohort")
    assert completed.returncode == 2
    assert "No cohorts selected" in completed.stderr


def test_invalid_cohort_schema_does_not_silently_pass(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "cohorts": [{"name": "bad", "expected_events": 3, "records": "oops"}],
    }), encoding="utf-8")
    completed = run_cli(str(path))
    assert completed.returncode == 2
    assert "records must be a list" in completed.stderr
