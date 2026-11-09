"""Batch reconciliation of synthetic trading events, without external services.

Validation and grouping belong to this orchestration layer. The existing
per-business-key Chain of Responsibility owns anomaly classification.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any, TypedDict

from data_qa.checkers.base import data_checkers
from data_qa.data.base import Record
from data_qa.data.trade_group import TradeGroup
from data_qa.data.trade_result import IssueCategories

Event = dict[str, Any]


class Issue(TypedDict):
    """One issue keyed by trade and account, or an unkeyed malformed row."""

    trade_id: str | None
    account_id: int | None
    details: dict[str, Any]


class ComparisonReport(TypedDict):
    missing: list[Issue]
    extra: list[Issue]
    changed: list[Issue]
    duplicates: list[Issue]
    malformed: list[Issue]


CATEGORIES = (
    IssueCategories.MISSING,
    IssueCategories.EXTRA,
    IssueCategories.CHANGED,
    IssueCategories.DUPLICATES,
    IssueCategories.MALFORMED,
)
REQUIRED_FIELDS = ("trade_id", "account_id", "version", "event_id", "status", "pnl")


def _evidence(value: Any) -> Any:
    """Detached JSON-like evidence. No caller input is mutated."""
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, (float, Decimal)):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): _evidence(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_evidence(item) for item in value]
    return repr(value)


def _validated_record(raw: Any) -> tuple[Record | None, list[str]]:
    """Reject invalid identity and payload instead of silently coercing them."""
    if not isinstance(raw, dict):
        return None, ["row must be a dictionary"]

    errors = [
        f"missing field: {field}"
        for field in REQUIRED_FIELDS if field not in raw
    ]
    trade_id, account_id = raw.get("trade_id"), raw.get("account_id")
    version, event_id = raw.get("version"), raw.get("event_id")
    status, pnl = raw.get("status"), raw.get("pnl")

    if not isinstance(trade_id, str) or not trade_id.strip():
        errors.append("trade_id must be a non-empty string")
    if type(account_id) is not int:
        errors.append("account_id must be an integer")
    if type(version) is not int or version <= 0:
        errors.append("version must be a positive integer")
    if not isinstance(event_id, str) or not event_id.strip():
        errors.append("event_id must be a non-empty string")
    if not isinstance(status, str) or not status.strip():
        errors.append("status must be a non-empty string")

    # Null PnL may be legitimate for certain lifecycle states; only presence
    # and numeric syntax are checked here, not status-specific business rules.
    if pnl is not None:
        if isinstance(pnl, bool) or not isinstance(pnl, (str, int, Decimal)):
            errors.append("pnl must be a numeric string, int, Decimal or null")
        else:
            try:
                if not Decimal(str(pnl)).is_finite():
                    errors.append("pnl must be finite")
            except (InvalidOperation, ValueError):
                errors.append("pnl must be numeric")

    if errors:
        return None, errors

    return Record(
        trade_id=trade_id,
        account_id=account_id,
        version=version,
        event_id=event_id,
        status=status,
        pnl=None if pnl is None else str(pnl),
    ), []


def _sort_key(issue: Issue) -> tuple[str, int, str]:
    return (
        issue["trade_id"] or "",
        issue["account_id"] if issue["account_id"] is not None else -1,
        json.dumps(issue["details"], sort_keys=True, ensure_ascii=False, default=str),
    )


def compare_events(source: list[Event], target: list[Event]) -> ComparisonReport:
    """Validate, group, run the chain and return deterministic diagnostics.

    Bad rows are retained as malformed. If a malformed row has a usable
    business key, the entire key is quarantined from normal reconciliation:
    otherwise a partial dataset can produce misleading missing/extra flags.
    """
    report: ComparisonReport = {
        "missing": [], "extra": [], "changed": [], "duplicates": [], "malformed": [],
    }
    groups: dict[tuple[str, int], TradeGroup] = {}
    quarantined: set[tuple[str, int]] = set()

    for side, rows in (("source", source), ("target", target)):
        for raw in rows:
            record, errors = _validated_record(raw)
            if errors:
                trade_id = (
                    raw.get("trade_id")
                    if isinstance(raw, dict)
                    and isinstance(raw.get("trade_id"), str)
                    and raw["trade_id"].strip()
                    else None
                )
                account_id = (
                    raw.get("account_id")
                    if isinstance(raw, dict) and type(raw.get("account_id")) is int
                    else None
                )
                if trade_id is not None and account_id is not None:
                    quarantined.add((trade_id, account_id))

                report["malformed"].append({
                    "trade_id": trade_id,
                    "account_id": account_id,
                    "details": {
                        "side": side, "reason": errors[0],
                        "errors": errors, "row": _evidence(raw),
                    },
                })
                continue

            assert record is not None
            key = record.business_key()
            group = groups.setdefault(key, TradeGroup(business_key=key))
            if side == "source":
                group.add_source(record)
            else:
                group.add_target(record)

    for key in sorted(groups):
        if key in quarantined:
            continue
        per_trade = groups[key].run_checks(data_checkers)
        for issue in per_trade.issues:
            report[issue.category].append({
                "trade_id": key[0],
                "account_id": key[1],
                "details": _evidence(issue.details),
            })

    for category in CATEGORIES:
        report[category].sort(key=_sort_key)
    return report
