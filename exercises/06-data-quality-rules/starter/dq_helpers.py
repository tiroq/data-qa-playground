"""Pure helpers for Session 06 DQ rules. No result/severity policy lives here."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from rule_result import RuleOutcome

Row = dict[str, Any]
BusinessKey = tuple[str, str]
IMMUTABLE_EVENT_FIELDS = (
    "trade_id", "account_id", "version", "status", "pnl", "event_time",
)
ALLOWED_STATUSES = frozenset({"NEW", "FILLED", "CANCELLED", "FAILED"})


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def positive_version(value: Any) -> bool:
    return type(value) is int and value > 0


def business_key(record: Row) -> BusinessKey | None:
    trade_id = record.get("trade_id")
    account_id = record.get("account_id")
    if valid_id(trade_id) and valid_id(account_id):
        return trade_id, account_id
    return None


def decimal_value(value: Any) -> Decimal | None:
    """Finite money values must be decimal strings; NULL remains separately valid."""
    if not isinstance(value, str):
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def parse_ts(value: Any) -> datetime | None:
    """Return an aware UTC timestamp; refuse naive or invalid timestamps."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def fingerprint(record: Row) -> str:
    """Immutable business event, excluding delivery metadata and event ID."""
    return json.dumps(
        {field: record.get(field) for field in IMMUTABLE_EVENT_FIELDS},
        ensure_ascii=False, sort_keys=True, default=str,
    )


def by_event_id(records: Iterable[Row]) -> dict[str, list[Row]]:
    grouped: dict[str, list[Row]] = defaultdict(list)
    for record in records:
        event_id = record.get("event_id")
        if valid_id(event_id):
            grouped[event_id].append(record)
    return dict(grouped)


def by_business_key(records: Iterable[Row]) -> dict[BusinessKey, list[Row]]:
    grouped: dict[BusinessKey, list[Row]] = defaultdict(list)
    for record in records:
        key = business_key(record)
        if key is not None:
            grouped[key].append(record)
    return dict(grouped)


def latest_version_rows(records: list[Row]) -> list[Row] | None:
    """None means version evidence is insufficient; never choose a tie arbitrarily."""
    if not records or any(not positive_version(r.get("version")) for r in records):
        return None
    latest = max(r["version"] for r in records)
    return [r for r in records if r["version"] == latest]


def emit(
    target: list[RuleOutcome],
    rule_id: str,
    severity: str,
    violations: list[dict[str, Any]] | None = None,
    uncertain: list[dict[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None,
) -> None:
    """Confirmed FAIL dominates incomplete coverage; preserve both kinds of evidence."""
    failed = list(violations or [])
    unknown = list(uncertain or [])
    status = "FAIL" if failed else "INDETERMINATE" if unknown else "PASS"
    target.append(RuleOutcome(
        rule_id=rule_id, status=status, severity=severity,
        issues=[*failed, *unknown], metrics=metrics or {},
    ))


def no_records(records: list[Row]) -> list[dict[str, Any]]:
    return [{"reason": "no_records_to_validate"}] if not records else []
