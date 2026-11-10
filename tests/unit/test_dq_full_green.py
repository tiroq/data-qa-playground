"""Runnable all-green evidence: every DQ rule must actually execute and pass."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "exercises/06-data-quality-rules/starter/rule_runner.py"
FIXTURE = ROOT / "exercises/06-data-quality-rules/fixtures/dq_full_green.json"


def test_fully_sourced_cohort_passes_all_20_rules() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER), str(FIXTURE), "--format", "json"],
        capture_output=True, text=True, cwd=ROOT, timeout=10,
    )
    assert proc.returncode == 0, proc.stderr + "\n" + proc.stdout
    output = json.loads(proc.stdout)
    assert output["summary"]["overall_status"] == "PASS"
    assert output["summary"]["implemented_rules"] == [f"DQ-{i:02}" for i in range(1, 21)]
    cohort = output["cohorts"][0]
    assert cohort["coverage_status"] == "COMPLETE"
    assert cohort["eligible_count"] == 2
    assert len(cohort["results"]) == 20
    assert all(row["status"] == "PASS" for row in cohort["results"])
    assert all(row["issues"] == [] for row in cohort["results"])
    assert next(r for r in cohort["results"] if r["rule_id"] == "DQ-08")[
        "metrics"]["on_time_count"] == 2
