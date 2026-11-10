"""Independent count-based completeness, SLA, freshness and empty-cohort rules."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from checkers import AbstractChecker
from dq_helpers import (
    by_event_id, emit, fingerprint, no_records, parse_ts, valid_id,
)
from rule_result import RuleOutcome

SLA_MINUTES = 10
SLA_MIN_PERCENT = 95


class ExpectedCompletenessChecker(AbstractChecker):
    """DQ-07: expected distinct event *cardinality* (not proof of identity).

    expected_event_ids, when present, permit membership verification. A count
    match alone cannot establish that the *correct* events were delivered.
    """

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        records = cohort["records"]
        expected = cohort["expected_events"]
        observed = set(by_event_id(records))
        invalid_ids = sum(not valid_id(r.get("event_id")) for r in records)
        failures: list[dict[str, Any]] = []
        unknown: list[dict[str, Any]] = []
        provided = cohort.get("expected_event_ids")
        if provided is not None:
            if not isinstance(provided, list) or not all(valid_id(v) for v in provided) \
                    or len(provided) != len(set(provided)) or len(provided) != expected:
                failures.append({"reason": "invalid_expected_event_catalog"})
            else:
                missing = sorted(set(provided) - observed)
                unexpected = sorted(observed - set(provided))
                if missing:
                    failures.append({"reason": "missing_expected_ids", "event_ids": missing})
                if unexpected:
                    failures.append({"reason": "unexpected_event_ids", "event_ids": unexpected})
        elif invalid_ids:
            unknown.append({
                "reason": "invalid_event_ids_limit_completeness",
                "invalid_rows": invalid_ids,
            })
        # Pure cardinality is still a measurable rule without a manifest.
        if len(observed) != expected:
            failures.append({
                "reason": "distinct_count_mismatch",
                "expected": expected, "observed": len(observed),
                "delta": len(observed) - expected,
            })
        if not records and expected == 0 and not cohort.get("allow_empty", False):
            unknown.append({"reason": "empty_cohort_requires_explicit_policy"})
        emit(result, "DQ-07", "critical", failures, unknown, {
            "expected_count": expected,
            "observed_distinct_count": len(observed),
            "denominator": expected,
            "identity_verified": provided is not None and not failures,
            "measurement": "event_cardinality",
        })
        return super().handle(cohort, result)


class VisibilitySLAChecker(AbstractChecker):
    """DQ-08: aggregate on-time visibility over matured *expected* events.

    A source-side expected_event_manifest with event_id/event_time is required.
    Missing source events with elapsed deadlines count as overdue. An observed
    event lacking an availability timestamp is *unknown*, not dropped from
    the denominator. Bounds decide PASS/FAIL/INDETERMINATE.
    """

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        manifest = cohort.get("expected_event_manifest")
        as_of = parse_ts(cohort.get("as_of"))
        metrics: dict[str, Any] = {
            "deadline_minutes": SLA_MINUTES,
            "on_time_threshold_percent": SLA_MIN_PERCENT,
            "denominator": "eligible_expected_distinct_events",
        }
        if manifest is None:
            emit(result, "DQ-08", "critical", uncertain=[{
                "reason": "missing_source_event_manifest",
                "message": "Expected event timestamps are required to measure SLA",
            }], metrics=metrics)
            return super().handle(cohort, result)
        if as_of is None or not isinstance(manifest, list):
            emit(result, "DQ-08", "critical", uncertain=[{
                "reason": "invalid_as_of_or_manifest",
            }], metrics=metrics)
            return super().handle(cohort, result)

        by_id: dict[str, Any] = {}
        manifest_errors = []
        for expected in manifest:
            if not isinstance(expected, dict) or not valid_id(expected.get("event_id")):
                manifest_errors.append({"reason": "invalid_manifest_entry"})
                continue
            event_id = expected["event_id"]
            event_time = parse_ts(expected.get("event_time"))
            if event_id in by_id or event_time is None:
                manifest_errors.append({"reason": "duplicate_or_invalid_manifest_event",
                                        "event_id": event_id})
                continue
            by_id[event_id] = event_time
        if len(by_id) != cohort["expected_events"]:
            manifest_errors.append({
                "reason": "manifest_count_mismatch",
                "expected": cohort["expected_events"], "actual": len(by_id),
            })
        if manifest_errors:
            emit(result, "DQ-08", "critical", violations=manifest_errors, metrics=metrics)
            return super().handle(cohort, result)

        deliveries = by_event_id(cohort["records"])
        on_time = 0
        late = 0
        overdue_missing = 0
        unknown = 0
        eligible = 0
        ambiguous_ids = []
        late_ids = []
        missing_ids = []
        for event_id, event_time in sorted(by_id.items()):
            deadline = event_time + timedelta(minutes=SLA_MINUTES)
            if event_time > as_of or deadline > as_of:
                continue
            eligible += 1
            records = deliveries.get(event_id, [])
            if not records:
                overdue_missing += 1
                missing_ids.append(event_id)
                continue
            if len({fingerprint(r) for r in records}) > 1:
                unknown += 1
                ambiguous_ids.append(event_id)
                continue
            timestamps = [parse_ts(r.get("available_at")) for r in records]
            known = [t for t in timestamps if t is not None and t <= as_of
                     and t >= event_time]
            # An observed invalid/null timestamp means the event might have
            # been visible on time even if a later valid receipt exists.
            if any(t is None for t in timestamps) and (
                not known or min(known) > deadline
            ):
                unknown += 1
                ambiguous_ids.append(event_id)
            elif any(t is not None and t < event_time for t in timestamps):
                unknown += 1
                ambiguous_ids.append(event_id)
            elif known and min(known) <= deadline:
                on_time += 1
            elif known:
                late += 1
                late_ids.append(event_id)
            else:
                # Receipts timestamped after as_of were not visible at cutoff.
                overdue_missing += 1
                missing_ids.append(event_id)

        metrics.update({
            "eligible_count": eligible,
            "on_time_count": on_time,
            "late_count": late,
            "overdue_unobserved_count": overdue_missing,
            "unknown_count": unknown,
            "lower_bound_percent": (100 * on_time / eligible) if eligible else None,
            "upper_bound_percent": (100 * (on_time + unknown) / eligible)
            if eligible else None,
        })
        if eligible == 0:
            emit(result, "DQ-08", "critical", uncertain=[{
                "reason": "no_matured_expected_events",
            }], metrics=metrics)
            return super().handle(cohort, result)

        issues = []
        if late_ids:
            issues.append({"reason": "late_events", "event_ids": late_ids})
        if missing_ids:
            issues.append({"reason": "overdue_missing_events", "event_ids": missing_ids})
        if ambiguous_ids:
            issues.append({"reason": "availability_unverifiable",
                           "event_ids": ambiguous_ids})

        # Classify by provable bounds, not by dropping unknowns from denominator.
        if (on_time + unknown) * 100 < SLA_MIN_PERCENT * eligible:
            emit(result, "DQ-08", "critical", violations=[
                {"reason": "sla_breach", "issues": issues}
            ], metrics=metrics)
        elif on_time * 100 >= SLA_MIN_PERCENT * eligible:
            emit(result, "DQ-08", "critical", metrics=metrics)
        else:
            emit(result, "DQ-08", "critical", uncertain=[
                {"reason": "sla_cannot_be_proven", "issues": issues}
            ], metrics=metrics)
        return super().handle(cohort, result)


class FreshnessChecker(AbstractChecker):
    """DQ-11: per-event latency defect, not the aggregate DQ-08 SLA."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        as_of = parse_ts(cohort.get("as_of"))
        violations = []
        unknown = no_records(cohort["records"])
        event_groups = by_event_id(cohort["records"])
        for event_id, records in sorted(event_groups.items()):
            if len({fingerprint(r) for r in records}) > 1:
                unknown.append({"event_id": event_id, "reason": "conflicting_event_time_or_payload"})
                continue
            event_time = parse_ts(records[0].get("event_time"))
            if as_of is None or event_time is None:
                unknown.append({"event_id": event_id, "reason": "invalid_or_missing_event_time"})
                continue
            valid_receipts = [parse_ts(r.get("available_at")) for r in records]
            if any(r is not None and r < event_time for r in valid_receipts):
                violations.append({"event_id": event_id, "reason": "negative_availability_lag"})
                continue
            receipts = [t for t in valid_receipts if t is not None and t <= as_of]
            if not receipts:
                unknown.append({"event_id": event_id, "reason": "availability_not_confirmed"})
                continue
            first = min(receipts)
            lag_seconds = (first - event_time).total_seconds()
            if lag_seconds > SLA_MINUTES * 60:
                # Unknown earlier observation could make actual lag shorter.
                if any(t is None for t in valid_receipts):
                    unknown.append({"event_id": event_id, "reason": "earlier_delivery_uncertain"})
                else:
                    violations.append({
                        "event_id": event_id, "reason": "late_event",
                        "lag_seconds": lag_seconds, "threshold_seconds": SLA_MINUTES * 60,
                    })
        if any(not valid_id(r.get("event_id")) for r in cohort["records"]):
            unknown.append({"reason": "invalid_event_ids_limit_freshness"})
        emit(result, "DQ-11", "warning", violations, unknown, {
            "threshold_seconds": SLA_MINUTES * 60,
            "evaluated_distinct_events": len(event_groups),
        })
        return super().handle(cohort, result)


class EmptyCohortChecker(AbstractChecker):
    """DQ-12: zero-row classification, separate from DQ-01 field validation."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        records = cohort["records"]
        expected = cohort["expected_events"]
        violations = []
        unknown = []
        if not records and expected > 0:
            violations.append({"reason": "unexpected_empty_batch",
                               "expected_events": expected})
        elif not records and not cohort.get("allow_empty", False):
            unknown.append({"reason": "explicit_allow_empty_required"})
        emit(result, "DQ-12", "critical", violations, unknown, {
            "physical_records": len(records), "expected_events": expected,
        })
        return super().handle(cohort, result)
