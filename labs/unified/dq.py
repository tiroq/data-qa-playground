"""Independent, pure-Python comparison of source manifest vs ClickHouse raw rows.

No broker/sink side effects. A PASS means the *observed snapshot* matches the
manifest; it is not proof that no later delivery will arrive.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

PAYLOAD_FIELDS = ("trade_id", "account_id", "version", "status", "pnl", "event_time")


def normal_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def field_equal(field: str, first: Any, second: Any) -> bool:
    if field == "pnl":
        try:
            return Decimal(str(first)) == Decimal(str(second))
        except (InvalidOperation, TypeError, ValueError):
            return False
    if field == "version":
        return int(first) == int(second)
    if field == "event_time":
        try:
            return normal_time(first) == normal_time(second)
        except (ValueError, TypeError):
            return False
    return first == second


def evaluate(run_id: str, planned_count: int,
             expected: list[dict], actual: list[dict]) -> dict:
    issues: list[dict] = []
    source_ids = [e.get("event_id") for e in expected]
    if planned_count <= 0 or not expected or len(expected) != planned_count:
        return {"run_id": run_id, "status": "ERROR", "issues": [
            {"rule":"invalid_manifest","detail":"Missing/empty or count-inconsistent authoritative source manifest"}],
            "planned_count":planned_count,"expected_distinct":len(set(source_ids)),
            "observed_distinct":0,"observed_physical":len(actual),"duplicate_deliveries":{}}
    if any(not e.get("event_id") for e in expected) or len(set(source_ids)) != len(source_ids):
        return {"run_id":run_id,"status":"ERROR","issues":[
            {"rule":"invalid_manifest","detail":"Duplicate or null expected event IDs"}],
            "planned_count":planned_count,"expected_distinct":len(set(source_ids)),
            "observed_distinct":0,"observed_physical":len(actual),"duplicate_deliveries":{}}
    expected_by_id = {e["event_id"]:e for e in expected}
    actual_by_id: dict[str,list[dict]] = defaultdict(list)
    for row in actual:
        actual_by_id[str(row.get("event_id"))].append(row)
        if row.get("run_id") != run_id:
            issues.append({"rule":"wrong_run_id","event_id":row.get("event_id")})
        if row.get("source_tag") != "flink_sql":
            issues.append({"rule":"invalid_source_tag","event_id":row.get("event_id")})
    missing = sorted(set(expected_by_id) - set(actual_by_id))
    unexpected = sorted(set(actual_by_id) - set(expected_by_id))
    if missing:
        issues.append({"rule":"missing_event","event_ids":missing})
    if unexpected:
        issues.append({"rule":"unexpected_event","event_ids":unexpected})
    duplicates = {eid:len(rows)-1 for eid,rows in actual_by_id.items() if len(rows)>1}
    for eid, rows in actual_by_id.items():
        source = expected_by_id.get(eid)
        if source is None:
            continue
        for row in rows:
            mismatches = [name for name in PAYLOAD_FIELDS
                          if not field_equal(name, source[name], row.get(name))]
            if mismatches:
                issues.append({"rule":"payload_mismatch","event_id":eid,"fields":mismatches})
    # Check all maximum-version rows before any representative selection.
    # Also flag non-max-version conflicts at the same version: raw history is auditable.
    groups: dict[tuple[str,str,int],set[tuple[str,str]]] = defaultdict(set)
    for row in actual:
        try:
            key = (str(row["account_id"]), str(row["trade_id"]), int(row["version"]))
            groups[key].add((str(row["status"]), str(Decimal(str(row["pnl"])).normalize())))
        except (KeyError, InvalidOperation, TypeError, ValueError):
            issues.append({"rule":"invalid_target_record","event_id":row.get("event_id")})
    for (account,trade,version),states in sorted(groups.items()):
        if len(states) > 1:
            issues.append({"rule":"conflict_same_version","business_key":[trade,account],
                           "version":version,"distinct_payloads":len(states)})
    return {"run_id":run_id, "status":"FAIL" if issues else "PASS",
            "issues":issues,"planned_count":planned_count,
            "expected_distinct":len(expected_by_id),
            "observed_distinct":len(actual_by_id),
            "observed_physical":len(actual),
            "duplicate_deliveries":duplicates}
