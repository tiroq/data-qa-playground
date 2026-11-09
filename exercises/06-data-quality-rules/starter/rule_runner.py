"""Session 06: execute implemented DQ checks and report per-cohort results.

From the repository root:
  python exercises/06-data-quality-rules/starter/rule_runner.py
  python exercises/06-data-quality-rules/starter/rule_runner.py --format json
  python exercises/06-data-quality-rules/starter/rule_runner.py --cohort mostly_healthy
  python exercises/06-data-quality-rules/starter/rule_runner.py --format json --output dq-report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from checkers import FieldsChecker
from rule_result import RuleOutcome, Status

DEFAULT_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "dq_batches.json"


def load_cohorts(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Unsupported fixture schema")
    cohorts = payload.get("cohorts")
    if not isinstance(cohorts, list):
        raise ValueError("cohorts must be a list")
    return cohorts


def evaluate_rules(cohort: dict[str, Any]) -> list[RuleOutcome]:
    """Execute only rules which have an actual implementation.

    Add subsequent checkers to this chain as they are implemented.
    Do not invent PASS results for DQ-02 or other future rules.
    """
    outcomes: list[RuleOutcome] = []
    FieldsChecker().handle(cohort, outcomes)
    if not outcomes:
        raise RuntimeError("No DQ rules executed; refusing a vacuous PASS")
    rule_ids = [outcome.rule_id for outcome in outcomes]
    if len(rule_ids) != len(set(rule_ids)):
        raise RuntimeError("Duplicate rule_id emitted by DQ checkers")
    return outcomes


def evaluate_cohort(cohort: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cohort, dict):
        raise ValueError("each cohort must be a JSON object")
    name = cohort.get("name")
    expected = cohort.get("expected_events")
    records = cohort.get("records")
    if not isinstance(name, str) or not name:
        raise ValueError("cohort name must be a nonempty string")
    if type(expected) is not int or expected < 0:
        raise ValueError(f"{name}: expected_events must be a nonnegative integer")
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError(f"{name}: records must be a list of JSON objects")

    outcomes = evaluate_rules(cohort)
    observed_ids = {
        r["event_id"] for r in records
        if isinstance(r.get("event_id"), str) and r["event_id"]
    }
    if not records:
        input_status: Status = "FAIL" if expected > 0 else "INDETERMINATE"
        reason = "unexpected_empty_batch" if expected > 0 else "empty_batch_no_evidence"
        input_issues = [{"reason": reason, "expected_events": expected,
                         "message": "No physical records were received"}]
    else:
        input_status = "PASS"
        input_issues = []

    if input_status == "FAIL" or any(
        r.status == "FAIL" and r.severity == "critical" for r in outcomes
    ):
        overall: Status = "FAIL"
    elif input_status == "INDETERMINATE" or any(
        r.status == "INDETERMINATE" for r in outcomes
    ):
        overall = "INDETERMINATE"
    else:
        overall = "PASS"

    return {
        "cohort": name,
        "as_of": cohort.get("as_of"),
        "expected_events": expected,
        "physical_records": len(records),
        "observed_distinct_event_ids": len(observed_ids),
        "input_gate": {"status": input_status, "issues": input_issues},
        "results": [asdict(r) for r in outcomes],
        "overall_status": overall,
    }


def build_report(cohorts: list[dict[str, Any]]) -> dict[str, Any]:
    if not cohorts:
        raise ValueError("No cohorts selected; refusing an empty report")
    reports = [evaluate_cohort(cohort) for cohort in cohorts]
    statuses = [report["overall_status"] for report in reports]
    overall = (
        "FAIL" if "FAIL" in statuses else
        "INDETERMINATE" if "INDETERMINATE" in statuses else "PASS"
    )
    return {
        "summary": {
            "overall_status": overall,
            "cohorts": len(reports),
            "pass": statuses.count("PASS"),
            "fail": statuses.count("FAIL"),
            "indeterminate": statuses.count("INDETERMINATE"),
            "implemented_rules": sorted({
                rule["rule_id"] for cohort in reports for rule in cohort["results"]
            }),
        },
        "cohorts": reports,
    }


def format_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f'Data Quality Report: {summary["overall_status"]}',
        f'Cohorts: {summary["cohorts"]} | PASS: {summary["pass"]} '
        f'| FAIL: {summary["fail"]} | INDETERMINATE: {summary["indeterminate"]}',
        "Implemented checks: " + ", ".join(summary["implemented_rules"]),
    ]
    for cohort in report["cohorts"]:
        lines.extend([
            "",
            f'[{cohort["overall_status"]}] {cohort["cohort"]}',
            f'  as_of={cohort["as_of"]} expected_events={cohort["expected_events"]} '
            f'physical_records={cohort["physical_records"]} '
            f'observed_distinct_event_ids={cohort["observed_distinct_event_ids"]}',
            f'  Input gate: {cohort["input_gate"]["status"]}',
        ])
        for issue in cohort["input_gate"]["issues"]:
            lines.append(f'    - {issue["reason"]}: {issue["message"]}')
        for rule in cohort["results"]:
            lines.append(
                f'  {rule["rule_id"]}: {rule["status"]} '
                f'(severity={rule["severity"]}, issues={len(rule["issues"])})'
            )
            for issue in rule["issues"]:
                detail = ", ".join(f"{key}={value}" for key, value in issue.items())
                lines.append(f"    - {detail}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run implemented Session 06 DQ checks")
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--cohort", help="Evaluate only the named cohort")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output", type=Path, help="Also save the report to this file")
    args = parser.parse_args(argv)
    try:
        cohorts = load_cohorts(args.fixture)
        if args.cohort is not None:
            cohorts = [c for c in cohorts
                       if isinstance(c, dict) and c.get("name") == args.cohort]
        report = build_report(cohorts)
        rendered = (
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            if args.format == "json" else format_text(report)
        )
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError, TypeError) as exc:
        print(f"DQ runner error: {exc}", file=sys.stderr)
        return 2
    print(rendered, end="")
    return 0 if report["summary"]["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
