"""Best-effort batch reconciliation with explicit check coverage.

Existing compare_events() callers still receive the five issue categories.
compare_events_detailed() additionally explains which checks are partial or
blocked by malformed records that may belong to each business key.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, TypedDict

from data_qa.checkers.base import data_checkers
from data_qa.data.base import Record, pnl_value
from data_qa.data.check_context import CheckContext, SideQuality
from data_qa.data.trade_group import AmbiguousLatestVersionError, TradeGroup
from data_qa.data.trade_result import IssueCategories

Event = dict[str, Any]
CheckStatus = Literal["complete", "partial", "blocked"]


class Issue(TypedDict):
    trade_id: str | None
    account_id: int | None
    details: dict[str, Any]


class ComparisonReport(TypedDict):
    missing: list[Issue]
    extra: list[Issue]
    changed: list[Issue]
    duplicates: list[Issue]
    malformed: list[Issue]


class CoverageEntry(TypedDict):
    trade_id: str
    account_id: int
    checks: dict[str, CheckStatus]


class CoverageReport(TypedDict):
    business_keys: list[CoverageEntry]
    unkeyed_malformed_count: int


class DetailedComparison(TypedDict):
    report: ComparisonReport
    coverage: CoverageReport


CATEGORIES = (
    IssueCategories.MISSING,
    IssueCategories.EXTRA,
    IssueCategories.CHANGED,
    IssueCategories.DUPLICATES,
    IssueCategories.MALFORMED,
)
REQUIRED_FIELDS = ("trade_id", "account_id", "version", "event_id", "status", "pnl")


@dataclass(frozen=True, slots=True)
class InvalidObservation:
    side: Literal["source", "target"]
    trade_id: str | None
    account_id: int | None
    version: int | None

    @property
    def key(self) -> tuple[str, int] | None:
        if self.trade_id is not None and self.account_id is not None:
            return self.trade_id, self.account_id
        return None


def _evidence(value: Any) -> Any:
    """Detach evidence from mutable input and allow stable JSON serialization."""
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
    if not isinstance(raw, dict):
        return None, ["row must be a dictionary"]

    errors = [f"missing field: {f}" for f in REQUIRED_FIELDS if f not in raw]
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

    # Status-specific PnL nullability is intentionally not a structural rule.
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


def _identity(raw: Any) -> tuple[str | None, int | None, int | None]:
    if not isinstance(raw, dict):
        return None, None, None
    trade_id = raw.get("trade_id")
    account_id = raw.get("account_id")
    version = raw.get("version")
    return (
        trade_id if isinstance(trade_id, str) and trade_id.strip() else None,
        account_id if type(account_id) is int else None,
        version if type(version) is int and version > 0 else None,
    )


def _sort_key(issue: Issue) -> tuple[str, int, str]:
    return (
        issue["trade_id"] or "",
        issue["account_id"] if issue["account_id"] is not None else -1,
        json.dumps(issue["details"], sort_keys=True, ensure_ascii=False, default=str),
    )


def _side_quality(
    observations: list[InvalidObservation], records: list[Record]
) -> SideQuality:
    if not observations:
        return SideQuality()
    max_valid_version = max((record.version for record in records), default=None)
    # If the invalid row has a known, older version, it cannot affect latest().
    # An unknown or >= latest version may change current state or version order.
    could_change_latest = any(
        obs.version is None
        or max_valid_version is None
        or obs.version >= max_valid_version
        for obs in observations
    )
    return SideQuality(possibly_excluded=True, latest_uncertain=could_change_latest)


def _latest_unambiguous(group: TradeGroup, side: Literal["source", "target"]) -> bool:
    try:
        return group.latest(side) is not None
    except AmbiguousLatestVersionError:
        return False


def _coverage(group: TradeGroup, context: CheckContext) -> dict[str, CheckStatus]:
    """Distinguish confirmed checks from checks limited by missing evidence."""
    has_source = bool(group.source)
    has_target = bool(group.target)
    possible_missing_side = (
        (not has_source and context.source.possibly_excluded)
        or (not has_target and context.target.possibly_excluded)
    )
    any_valid = has_source or has_target
    complete_population = not (
        context.source.possibly_excluded or context.target.possibly_excluded
    )
    latest_safe = (
        has_source
        and has_target
        and not context.source.latest_uncertain
        and not context.target.latest_uncertain
        and _latest_unambiguous(group, "source")
        and _latest_unambiguous(group, "target")
    )
    return {
        "presence": "blocked" if possible_missing_side else "complete",
        "duplicates": (
            "complete" if complete_population else "partial" if any_valid else "blocked"
        ),
        "payload_conflict": (
            "complete" if complete_population else "partial" if any_valid else "blocked"
        ),
        "state_mismatch": "complete" if latest_safe else "blocked",
        "version_mismatch": "complete" if latest_safe else "blocked",
    }


def _run(source: list[Event], target: list[Event]) -> DetailedComparison:
    report: ComparisonReport = {category: [] for category in CATEGORIES}  # type: ignore[typeddict-item]
    groups: dict[tuple[str, int], TradeGroup] = {}
    invalid_full: dict[tuple[str, int], list[InvalidObservation]] = defaultdict(list)
    invalid_trade: dict[str, list[InvalidObservation]] = defaultdict(list)
    invalid_account: dict[int, list[InvalidObservation]] = defaultdict(list)
    invalid_unknown: list[InvalidObservation] = []
    coverage_keys: set[tuple[str, int]] = set()

    for side, rows in (("source", source), ("target", target)):
        for raw in rows:
            record, errors = _validated_record(raw)
            if errors:
                trade_id, account_id, version = _identity(raw)
                observation = InvalidObservation(side, trade_id, account_id, version)
                if observation.key is not None:
                    invalid_full[observation.key].append(observation)
                    coverage_keys.add(observation.key)
                elif trade_id is not None:
                    invalid_trade[trade_id].append(observation)
                elif account_id is not None:
                    invalid_account[account_id].append(observation)
                else:
                    invalid_unknown.append(observation)

                report["malformed"].append({
                    "trade_id": trade_id,
                    "account_id": account_id,
                    "details": {
                        "side": side,
                        "reason": errors[0],
                        "errors": errors,
                        "row": _evidence(raw),
                    },
                })
                continue

            assert record is not None
            key = record.business_key()
            coverage_keys.add(key)
            group = groups.setdefault(key, TradeGroup(business_key=key))
            if side == "source":
                group.add_source(record)
            else:
                group.add_target(record)

    coverage_entries: list[CoverageEntry] = []
    for key in sorted(coverage_keys):
        group = groups.get(key)
        if group is None:
            group = TradeGroup(business_key=key)

        # Known partial identities only impact plausible matching business keys.
        relevant = [
            *invalid_full.get(key, ()),
            *invalid_trade.get(key[0], ()),
            *invalid_account.get(key[1], ()),
            *invalid_unknown,
        ]
        ctx = CheckContext(
            source=_side_quality(
                [obs for obs in relevant if obs.side == "source"], group.source
            ),
            target=_side_quality(
                [obs for obs in relevant if obs.side == "target"], group.target
            ),
        )
        group.context = ctx

        coverage_entries.append({
            "trade_id": key[0],
            "account_id": key[1],
            "checks": _coverage(group, ctx),
        })

        if not group.source and not group.target:
            # A malformed-only key has no valid records to run through the chain.
            continue

        per_trade = group.run_checks(data_checkers)
        for issue in per_trade.issues:
            report[issue.category].append({
                "trade_id": key[0],
                "account_id": key[1],
                "details": _evidence(issue.details),
            })

    for category in CATEGORIES:
        report[category].sort(key=_sort_key)

    return {
        "report": report,
        "coverage": {
            "business_keys": coverage_entries,
            "unkeyed_malformed_count": sum(
                len(items) for items in invalid_trade.values()
            ) + sum(len(items) for items in invalid_account.values()) + len(invalid_unknown),
        },
    }


def compare_events(source: list[Event], target: list[Event]) -> ComparisonReport:
    """Return five issue categories; continue valid checks after malformed input."""
    return _run(source, target)["report"]


def compare_events_detailed(
    source: list[Event], target: list[Event]
) -> DetailedComparison:
    """Return findings and per-key coverage (complete/partial/blocked).

    Incomplete rows limit specific conclusions, but do not erase confirmed
    duplicates, internal payload conflicts or other supported findings.
    """
    return _run(source, target)
