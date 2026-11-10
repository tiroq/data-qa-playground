"""Independent source/target checks. No event-replay semantics are reused here.

These checkers need extra source_records/target_records. Missing prerequisites
produce INDETERMINATE instead of reporting fictitious PASS.
"""
from __future__ import annotations

from typing import Any

from checkers import AbstractChecker
from dq_helpers import (
    ALLOWED_STATUSES, business_key, by_business_key, decimal_value,
    emit, fingerprint, latest_version_rows,
)
from rule_result import RuleOutcome


def paired(cohort: dict[str, Any]) -> tuple[list[dict], list[dict]] | None:
    source, target = cohort.get("source_records"), cohort.get("target_records")
    if not isinstance(source, list) or not isinstance(target, list):
        return None
    return source, target


def current_state(rows: list[dict]) -> tuple[dict | None, str | None]:
    latest = latest_version_rows(rows)
    if latest is None:
        return None, "invalid_or_missing_version"
    # Two distinct payloads in same version are not deterministically orderable.
    if len({fingerprint(row) for row in latest}) > 1:
        return None, "ambiguous_latest_version"
    return latest[0], None


class SourceTargetLifecycleChecker(AbstractChecker):
    """DQ-10: compare status only, for matching keys at the same latest version.

    Presence, version lag, PnL and FAILED-as-a-signal are separate DQ rules.
    """

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        data = paired(cohort)
        if data is None:
            emit(result, "DQ-10", "critical", uncertain=[{"reason": "source_target_required"}])
            return super().handle(cohort, result)
        source, target = data
        source_keys, target_keys = by_business_key(source), by_business_key(target)
        failures, unknown = [], []
        common = sorted(source_keys.keys() & target_keys.keys())
        if not common:
            unknown.append({"reason": "no_matched_business_keys"})
        for key in common:
            lhs, lerr = current_state(source_keys[key])
            rhs, rerr = current_state(target_keys[key])
            if lerr or rerr:
                unknown.append({"trade_id": key[0], "account_id": key[1],
                                "reason": "ambiguous_latest", "source": lerr, "target": rerr})
                continue
            assert lhs is not None and rhs is not None
            if lhs["version"] != rhs["version"]:
                unknown.append({"trade_id": key[0], "account_id": key[1],
                                "reason": "different_versions_deferred_to_DQ-17"})
            elif lhs.get("status") not in ALLOWED_STATUSES or rhs.get("status") not in ALLOWED_STATUSES:
                unknown.append({"trade_id": key[0], "account_id": key[1],
                                "reason": "invalid_status_blocks_comparison"})
            elif lhs["status"] != rhs["status"]:
                failures.append({"trade_id": key[0], "account_id": key[1],
                                 "version": lhs["version"],
                                 "source_status": lhs["status"],
                                 "target_status": rhs["status"],
                                 "reason": "lifecycle_status_mismatch"})
        if any(business_key(r) is None for r in [*source, *target]):
            unknown.append({"reason": "invalid_side_keys_limit_coverage"})
        emit(result, "DQ-10", "critical", failures, unknown, {"matched_keys": len(common)})
        return super().handle(cohort, result)


class SourceTargetPresenceChecker(AbstractChecker):
    """DQ-14: MISSING / ORPHAN after explicit reconciliation cutoff only."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        data = paired(cohort)
        if data is None or cohort.get("reconciliation_finalized") is not True:
            emit(result, "DQ-14", "critical", uncertain=[{
                "reason": "source_target_and_finalized_cutoff_required"
            }])
            return super().handle(cohort, result)
        source, target = data
        source_keys, target_keys = set(by_business_key(source)), set(by_business_key(target))
        invalid_source = any(business_key(row) is None for row in source)
        invalid_target = any(business_key(row) is None for row in target)
        failures, unknown = [], []
        for key in sorted(source_keys - target_keys):
            entry = {"trade_id": key[0], "account_id": key[1], "reason": "MISSING"}
            (unknown if invalid_target else failures).append(entry)
        for key in sorted(target_keys - source_keys):
            entry = {"trade_id": key[0], "account_id": key[1], "reason": "ORPHAN"}
            (unknown if invalid_source else failures).append(entry)
        if not source and not target:
            unknown.append({"reason": "both_sides_empty"})
        emit(result, "DQ-14", "critical", failures, unknown, {
            "source_distinct_keys": len(source_keys),
            "target_distinct_keys": len(target_keys),
            "cutoff_finalized": True,
        })
        return super().handle(cohort, result)


class ProcessedSnapshotUniquenessChecker(AbstractChecker):
    """DQ-15: repeated business keys in a target *snapshot* table.

    Never apply the rule to a target event log, where several versions
    of one trade are expected.
    """

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        target = cohort.get("target_records")
        if not isinstance(target, list) or cohort.get("target_grain") != "snapshot":
            emit(result, "DQ-15", "critical", uncertain=[{
                "reason": "target_snapshot_grain_required"
            }])
            return super().handle(cohort, result)
        failures = []
        for key, rows in sorted(by_business_key(target).items()):
            if len(rows) > 1:
                failures.append({
                    "trade_id": key[0], "account_id": key[1],
                    "processing_count": len(rows),
                    "reason": "duplicate_processing_snapshot_key",
                })
        unknown = []
        if any(business_key(row) is None for row in target):
            unknown.append({"reason": "invalid_target_keys_limit_uniqueness"})
        if not target and not cohort.get("allow_empty", False):
            unknown.append({"reason": "empty_target_snapshot"})
        emit(result, "DQ-15", "critical", failures, unknown, {
            "snapshot_business_key_count": len(by_business_key(target)),
        })
        return super().handle(cohort, result)


class CrossSideVersionChecker(AbstractChecker):
    """DQ-17: latest source/target version mismatch, not internal version conflict."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        data = paired(cohort)
        if data is None:
            emit(result, "DQ-17", "critical", uncertain=[{
                "reason": "source_target_required"
            }])
            return super().handle(cohort, result)
        source, target = data
        src, dst = by_business_key(source), by_business_key(target)
        matched = sorted(src.keys() & dst.keys())
        failures, unknown = [], []
        if not matched:
            unknown.append({"reason": "no_matched_business_keys"})
        for key in matched:
            lhs, le = current_state(src[key])
            rhs, re = current_state(dst[key])
            if le or re:
                unknown.append({"trade_id": key[0], "account_id": key[1],
                                "reason": "latest_version_ambiguous"})
                continue
            assert lhs is not None and rhs is not None
            if lhs["version"] != rhs["version"]:
                failures.append({
                    "trade_id": key[0], "account_id": key[1],
                    "source_version": lhs["version"],
                    "target_version": rhs["version"],
                    "reason": "latest_version_mismatch",
                })
        emit(result, "DQ-17", "critical", failures, unknown, {"matched_keys": len(matched)})
        return super().handle(cohort, result)


class FailedProcessingChecker(AbstractChecker):
    """DQ-18: explicit failed target executions, not missing events."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        target = cohort.get("target_records")
        if not isinstance(target, list):
            emit(result, "DQ-18", "warning", uncertain=[{"reason": "target_records_required"}])
            return super().handle(cohort, result)
        failures = [
            {"trade_id": row.get("trade_id"), "account_id": row.get("account_id"),
             "event_id": row.get("event_id"), "reason": "processing_failed"}
            for row in target if row.get("status") == "FAILED"
        ]
        unknown = [{"reason": "empty_target_input"}] if not target else []
        emit(result, "DQ-18", "warning", failures, unknown, {
            "failed_rows": len(failures), "target_rows": len(target),
        })
        return super().handle(cohort, result)


class UnknownProcessingStatusChecker(AbstractChecker):
    """DQ-19: unknown/NULL processing status, independent of FAILED count."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        target = cohort.get("target_records")
        if not isinstance(target, list):
            emit(result, "DQ-19", "critical", uncertain=[{"reason": "target_records_required"}])
            return super().handle(cohort, result)
        failures = [
            {"trade_id": row.get("trade_id"), "account_id": row.get("account_id"),
             "status": row.get("status"), "reason": "unknown_processing_status"}
            for row in target if row.get("status") is None or
            row.get("status") not in (ALLOWED_STATUSES | {"SUCCESS"})
        ]
        emit(result, "DQ-19", "critical", failures,
             [{"reason": "empty_target_input"}] if not target else [])
        return super().handle(cohort, result)


class SourceTargetPnlChecker(AbstractChecker):
    """DQ-20: latest-version numerical PnL reconciliation, separate from status."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        data = paired(cohort)
        if data is None:
            emit(result, "DQ-20", "critical", uncertain=[{"reason": "source_target_required"}])
            return super().handle(cohort, result)
        source, target = data
        src, dst = by_business_key(source), by_business_key(target)
        failures, unknown = [], []
        for key in sorted(src.keys() & dst.keys()):
            lhs, lerr = current_state(src[key])
            rhs, rerr = current_state(dst[key])
            if lerr or rerr or lhs is None or rhs is None:
                unknown.append({"trade_id": key[0], "account_id": key[1],
                                "reason": "ambiguous_latest_blocks_pnl_comparison"})
                continue
            if lhs["version"] != rhs["version"]:
                unknown.append({"trade_id": key[0], "account_id": key[1],
                                "reason": "version_mismatch_blocks_pnl_comparison"})
                continue
            left_pnl, right_pnl = lhs.get("pnl"), rhs.get("pnl")
            if left_pnl is not None and decimal_value(left_pnl) is None or (
                right_pnl is not None and decimal_value(right_pnl) is None
            ):
                unknown.append({"trade_id": key[0], "account_id": key[1],
                                "reason": "invalid_decimal_blocks_comparison"})
                continue
            if (decimal_value(left_pnl) if left_pnl is not None else None) != (
                decimal_value(right_pnl) if right_pnl is not None else None
            ):
                failures.append({
                    "trade_id": key[0], "account_id": key[1],
                    "version": lhs["version"], "source_pnl": left_pnl,
                    "target_pnl": right_pnl, "reason": "latest_pnl_mismatch",
                })
        if not src.keys() & dst.keys():
            unknown.append({"reason": "no_matched_business_keys"})
        emit(result, "DQ-20", "critical", failures, unknown)
        return super().handle(cohort, result)
