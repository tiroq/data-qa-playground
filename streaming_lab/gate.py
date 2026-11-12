"""Independent source-manifest vs ClickHouse raw-event Data Quality gate.

Offline/pure Python logic: the shell orchestrator exports JSONL using database
native CLIs. A green seed/connection smoke is NOT a DQ verdict.

Exit codes: 0=PASS, 2=confirmed FAIL, 3=INDETERMINATE, 4=SETUP_ERROR.
Duplicate physical deliveries with the exact same event and payload are warnings,
not extra logical events. Contradictory payloads are critical failures.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

EXIT_CODES = {"PASS": 0, "FAIL": 2, "INDETERMINATE": 3, "SETUP_ERROR": 4}
FIELDS = ("run_id", "event_id", "trade_id", "account_id",
          "version", "pnl", "status", "event_time_ms")
SLA_MS = 10 * 60 * 1000


def money(value: Any) -> Decimal | None:
    try:
        if isinstance(value, bool) or value is None:
            return None
        number = Decimal(str(value))
        return number if number.is_finite() else None
    except (ValueError, InvalidOperation, TypeError):
        return None


def business_payload(row: dict) -> tuple:
    value = money(row.get("pnl"))
    return (row.get("trade_id"), row.get("account_id"), row.get("version"),
            value, row.get("status"), row.get("event_time_ms"))


def read_available_at(row: dict) -> int | None:
    raw = row.get("available_at")
    if raw is None:
        return None
    try:
        if isinstance(raw, (float, int)):
            return int(raw)
        # ClickHouse's toString(DateTime64) is typically 2026-11-12 12:34:56.123
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except (ValueError, TypeError, OverflowError):
        return None


def inspect(manifest: dict | None, expected: list[dict], actual: list[dict],
            *, now_ms: int | None = None) -> dict:
    """Make a deterministic, machine-readable decision for a single run."""
    if now_ms is None:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    issues: list[dict] = []
    warnings: list[dict] = []

    def issue(rule: str, detail: str, **evidence: Any) -> None:
        issues.append({"rule": rule, "reason": detail, **evidence})

    def warn(rule: str, detail: str, **evidence: Any) -> None:
        warnings.append({"rule": rule, "reason": detail, **evidence})

    if manifest is None:
        return {"status": "INDETERMINATE", "reason": "missing_run_manifest",
                "issues": [], "warnings": [], "expected_count": len(expected),
                "actual_physical_count": len(actual), "sla": {"status": "INDETERMINATE"}}

    run_id = manifest.get("run_id")
    planned = manifest.get("planned_events")
    if not isinstance(run_id, str) or not run_id or type(planned) is not int or planned < 0:
        return {"status": "SETUP_ERROR", "reason": "invalid_run_manifest",
                "issues": [], "warnings": [], "sla": {"status": "INDETERMINATE"}}
    if not manifest.get("sealed", False):
        return {"run_id": run_id, "status": "INDETERMINATE",
                "reason": "producer_not_sealed", "issues": [], "warnings": [],
                "expected_count": len(expected), "actual_physical_count": len(actual),
                "sla": {"status": "INDETERMINATE"}}
    if planned == 0:
        issue("DQ-EMPTY", "unexpected empty planned cohort", run_id=run_id)
    if len(expected) != planned:
        issue("DQ-MANIFEST", "declared count does not match source manifest",
              planned_count=planned, source_count=len(expected))

    for side, records in (("source", expected), ("target", actual)):
        for row in records:
            if any(field not in row for field in FIELDS):
                issue("DQ-FIELDS", "required field missing", side=side,
                      event_id=row.get("event_id"))
                continue
            if row.get("run_id") != run_id:
                issue("DQ-RUN", "cross-run contamination", side=side,
                      event_id=row.get("event_id"))
            if not row.get("event_id") or not row.get("trade_id") or not row.get("account_id"):
                issue("DQ-KEY", "invalid immutable event or business key", side=side,
                      event_id=row.get("event_id"))
            if type(row.get("version")) is not int or row["version"] < 1:
                issue("DQ-VERSION", "invalid business version", side=side,
                      event_id=row.get("event_id"))
            if money(row.get("pnl")) is None:
                issue("DQ-DECIMAL", "invalid PnL decimal", side=side,
                      event_id=row.get("event_id"))

    expected_ids = [row.get("event_id") for row in expected]
    if len(expected_ids) != len(set(expected_ids)):
        issue("DQ-MANIFEST", "duplicate immutable event IDs in source of truth")
    source_map = {row.get("event_id"): row for row in expected}
    actual_by_id: dict[str | None, list[dict]] = defaultdict(list)
    for row in actual:
        actual_by_id[row.get("event_id")].append(row)

    missing = sorted((set(expected_ids) - set(actual_by_id)), key=str)
    unexpected = sorted((set(actual_by_id) - set(expected_ids)), key=str)
    if missing:
        issue("DQ-MISSING", "source events not visible in target raw history",
              event_ids=missing)
    if unexpected:
        issue("DQ-UNEXPECTED", "unplanned immutable event IDs in target",
              event_ids=unexpected)

    for event_id, versions in sorted(actual_by_id.items(), key=lambda item: str(item[0])):
        signatures = {business_payload(row) for row in versions}
        if len(signatures) > 1:
            issue("DQ-EVENT-CONFLICT", "same event ID with contradictory payload",
                  event_id=event_id, physical_count=len(versions))
        elif len(versions) > 1:
            warn("DQ-REDELIVERY", "identical physical deliveries of one event",
                 event_id=event_id, duplicate_count=len(versions) - 1)
        if event_id in source_map and any(
            business_payload(row) != business_payload(source_map[event_id])
            for row in versions
        ):
            issue("DQ-PAYLOAD", "target payload diverges from authoritative event",
                  event_id=event_id)

    for side, records in (("source", expected), ("target", actual)):
        by_trade_version: dict[tuple, set] = defaultdict(set)
        for row in records:
            key = (row.get("account_id"), row.get("trade_id"), row.get("version"))
            by_trade_version[key].add((row.get("status"), money(row.get("pnl"))))
        for key, signatures in by_trade_version.items():
            if len(signatures) > 1:
                issue("DQ-SAME-VERSION", "conflicting payloads share business version",
                      side=side, account_id=key[0], trade_id=key[1], version=key[2])

    # SLO is a separate independent dimension. A missing immature event remains
    # in-flight for SLA purposes; DQ-MISSING still prevents a final green gate.
    on_time = late = overdue = in_flight = 0
    for item in expected:
        if type(item.get("event_time_ms")) is not int:
            continue
        source_timestamp = item["event_time_ms"]
        observed = [read_available_at(row) for row in actual_by_id.get(item.get("event_id"), [])]
        seen = [timestamp for timestamp in observed if timestamp is not None]
        if seen:
            if min(seen) - source_timestamp <= SLA_MS:
                on_time += 1
            else:
                late += 1
        elif now_ms >= source_timestamp + SLA_MS:
            overdue += 1
        else:
            in_flight += 1
    population = on_time + late + overdue + in_flight
    if population == 0:
        sla_status = "INDETERMINATE"
    elif on_time / population >= 0.95:
        sla_status = "PASS"
    elif (on_time + in_flight) / population < 0.95:
        sla_status = "FAIL"
    else:
        sla_status = "INDETERMINATE"
    sla = {"status": sla_status, "on_time": on_time, "late": late,
           "overdue": overdue, "in_flight": in_flight,
           "denominator": population, "threshold": 0.95, "deadline_ms": SLA_MS,
           "clock_basis": "source_event_time_ms_vs_ClickHouse_available_at"}

    if sla_status == "FAIL":
        issue("DQ-SLA", "confirmed synthetic 95-percent visibility objective breached",
              **sla)

    return {"run_id": run_id, "status": "FAIL" if issues else
            ("INDETERMINATE" if sla_status == "INDETERMINATE" else "PASS"),
            "reason": "blocking_data_quality" if issues else
            ("insufficient_sla_evidence" if sla_status == "INDETERMINATE" else "verified"),
            "expected_count": len(expected),
            "actual_physical_count": len(actual),
            "distinct_actual_events": len(actual_by_id),
            "issues": sorted(issues, key=lambda e: (e["rule"], str(e.get("event_id", "")),
                                                    str(e.get("trade_id", "")))),
            "warnings": sorted(warnings, key=lambda e: (e["rule"], str(e.get("event_id", "")))),
            "sla": sla}


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    try:
        manifests = load_jsonl(args.manifest)
        if len(manifests) > 1:
            raise ValueError("expected at most one run manifest")
        report = inspect(manifests[0] if manifests else None,
                         load_jsonl(args.expected), load_jsonl(args.actual))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        report = {"status": "SETUP_ERROR", "reason": str(exc), "issues": [], "warnings": []}
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    print(rendered)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(EXIT_CODES[report["status"]])


if __name__ == "__main__":
    main()
