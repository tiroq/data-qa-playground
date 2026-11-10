"""Independent per-event and per-version checks (DQ-03/04/05/06/09/13/16).

Rules do not filter or rewrite the cohort. Every checker sees the original rows.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from checkers import AbstractChecker
from dq_helpers import (
    ALLOWED_STATUSES, business_key, by_business_key, by_event_id, decimal_value,
    emit, fingerprint, no_records, positive_version, valid_id,
)
from rule_result import RuleOutcome


class PayloadConsistencyChecker(AbstractChecker):
    """DQ-03: one immutable event_id must not represent conflicting payloads."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        records = cohort["records"]
        violations = []
        unknown = no_records(records)
        for event_id, deliveries in sorted(by_event_id(records).items()):
            signatures = {fingerprint(record) for record in deliveries}
            if len(signatures) > 1:
                violations.append({
                    "event_id": event_id,
                    "reason": "immutable_event_payload_conflict",
                    "distinct_payloads": len(signatures),
                    "delivery_count": len(deliveries),
                })
        if any(not valid_id(r.get("event_id")) for r in records):
            unknown.append({"reason": "invalid_event_identity_limits_coverage"})
        emit(result, "DQ-03", "critical", violations, unknown)
        return super().handle(cohort, result)


class VersionDomainChecker(AbstractChecker):
    """DQ-04: a supplied version must be a positive non-boolean integer."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        violations = []
        for index, record in enumerate(cohort["records"]):
            if record.get("version") is not None and not positive_version(record["version"]):
                violations.append({
                    "event_id": record.get("event_id"), "row_index": index,
                    "version": record["version"], "reason": "invalid_version",
                })
        emit(result, "DQ-04", "critical", violations, no_records(cohort["records"]))
        return super().handle(cohort, result)


class StatusDomainChecker(AbstractChecker):
    """DQ-05: a non-null status must be in the contract enum."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        violations = [
            {"event_id": row.get("event_id"), "status": row["status"],
             "reason": "unsupported_status"}
            for row in cohort["records"]
            if row.get("status") is not None and row["status"] not in ALLOWED_STATUSES
        ]
        emit(result, "DQ-05", "critical", violations, no_records(cohort["records"]))
        return super().handle(cohort, result)


class DecimalValidityChecker(AbstractChecker):
    """DQ-06: supplied non-null PnL must be a finite decimal string."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        violations = [
            {"event_id": row.get("event_id"), "pnl": row["pnl"],
             "reason": "invalid_decimal"}
            for row in cohort["records"]
            if row.get("pnl") is not None and decimal_value(row["pnl"]) is None
        ]
        unknown = no_records(cohort["records"])
        emit(result, "DQ-06", "critical", violations, unknown)
        return super().handle(cohort, result)


class VersionConsistencyChecker(AbstractChecker):
    """DQ-09: distinct events must not disagree on state at one business version.

    The same event_id with conflicting payload is exclusively DQ-03.
    New versions of the same trade are legitimate and are not deduplicated.
    """

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        violations: list[dict[str, Any]] = []
        unknown = no_records(cohort["records"])
        for key, records in sorted(by_business_key(cohort["records"]).items()):
            per_version: dict[int, list[dict[str, Any]]] = defaultdict(list)
            for row in records:
                if positive_version(row.get("version")) and valid_id(row.get("event_id")):
                    per_version[row["version"]].append(row)
            for version, at_version in sorted(per_version.items()):
                # Identical transport redeliveries must not inflate the distinct
                # event population, and DQ-03 owns conflicts within one ID.
                event_groups = by_event_id(at_version)
                if len(event_groups) < 2:
                    continue
                if any(len({fingerprint(r) for r in deliveries}) > 1
                       for deliveries in event_groups.values()):
                    unknown.append({
                        "trade_id": key[0], "account_id": key[1], "version": version,
                        "reason": "immutable_event_conflict_blocks_version_comparison",
                    })
                    continue
                states = set()
                for deliveries in event_groups.values():
                    representative = deliveries[0]
                    pnl = representative.get("pnl")
                    parsed_pnl = decimal_value(pnl) if pnl is not None else None
                    if pnl is not None and parsed_pnl is None:
                        unknown.append({
                            "trade_id": key[0], "account_id": key[1], "version": version,
                            "reason": "invalid_pnl_blocks_version_comparison",
                        })
                        states.clear()
                        break
                    states.add((representative.get("status"), parsed_pnl))
                if len(states) > 1:
                    violations.append({
                        "trade_id": key[0], "account_id": key[1], "version": version,
                        "event_ids": sorted(event_groups),
                        "reason": "conflicting_same_version_states",
                    })
        if any(business_key(r) is None or not positive_version(r.get("version"))
               for r in cohort["records"]):
            unknown.append({"reason": "invalid_business_key_or_version_limits_coverage"})
        emit(result, "DQ-09", "critical", violations, unknown)
        return super().handle(cohort, result)


class BusinessConsistencyChecker(AbstractChecker):
    """DQ-13: explicit status/PnL semantic invariant, separate from type checking.

    Training assumption: a FILLED trade must carry a PnL; NULL is permitted
    for NEW, CANCELLED and FAILED. Numerical format is exclusively DQ-06.
    """

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        violations = [
            {"event_id": row.get("event_id"), "status": "FILLED",
             "reason": "filled_trade_missing_pnl"}
            for row in cohort["records"]
            if row.get("status") == "FILLED" and row.get("pnl") is None
        ]
        emit(result, "DQ-13", "critical", violations, no_records(cohort["records"]))
        return super().handle(cohort, result)


class BusinessKeyValidityChecker(AbstractChecker):
    """DQ-16: ID type/blank validation; DQ-01 owns presence/null only."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        violations = []
        for index, row in enumerate(cohort["records"]):
            for field in ("event_id", "trade_id", "account_id"):
                if field in row and row[field] is not None and not valid_id(row[field]):
                    violations.append({
                        "event_id": row.get("event_id"), "row_index": index,
                        "field": field, "reason": "invalid_identifier",
                    })
        emit(result, "DQ-16", "critical", violations, no_records(cohort["records"]))
        return super().handle(cohort, result)
