from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from rule_result import RuleOutcome


class Checker(ABC):
    """Interface for independent data-quality checks in a chain."""

    @abstractmethod
    def set_next(self, handler: Checker) -> Checker:
        pass

    @abstractmethod
    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        pass


class AbstractChecker(Checker):
    """Call the next checker after the current rule finishes."""

    _next_handler: Checker | None = None

    def set_next(self, handler: Checker) -> Checker:
        self._next_handler = handler
        return handler

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        if self._next_handler:
            self._next_handler.handle(cohort, result)


class FieldsChecker(AbstractChecker):
    """DQ-01: report absent/null required fields for physical event records."""

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        # No physical records means this rule has not evaluated any fields.
        # A separate cohort-level input gate decides if the empty input is allowed.
        if not cohort["records"]:
            result.append(
                RuleOutcome(
                    rule_id="DQ-01",
                    status="INDETERMINATE",
                    severity="critical",
                    issues=[{
                        "reason": "no_records_to_validate",
                        "message": "No physical records to validate",
                    }],
                )
            )
            return super().handle(cohort, result)

        issues = []
        for record in cohort["records"]:
            for field in ["event_id", "trade_id", "account_id", "version", "status"]:
                if record.get(field, None) is None:
                    issues.append(
                        {
                            "event_id": record.get("event_id"),
                            "field": field,
                            "reason": "required_field_is_null",
                            "message": f"Required field '{field}' is null",
                        }
                    )

        result.append(
            RuleOutcome(
                rule_id="DQ-01",
                status="FAIL" if issues else "PASS",
                severity="critical",
                issues=issues,
            )
        )
        return super().handle(cohort, result)


class DuplicateChecker(AbstractChecker):
    """DQ-02: identical replay of an immutable event identity.

    Conflicting payloads with one event_id are deferred to DQ-03.
    available_at is delivery/observation metadata, not event payload.
    """

    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        import json
        from collections import defaultdict

        records = cohort["records"]
        if not records:
            result.append(RuleOutcome(
                rule_id="DQ-02",
                status="INDETERMINATE",
                severity="warning",
                issues=[{"reason": "no_records_to_validate"}],
            ))
            return super().handle(cohort, result)

        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        invalid_count = 0
        for record in records:
            event_id = record.get("event_id")
            if not isinstance(event_id, str) or not event_id.strip():
                invalid_count += 1
                continue
            groups[event_id].append(record)

        issues: list[dict[str, Any]] = []
        repeated = False
        uncertain = invalid_count > 0

        for event_id, deliveries in sorted(groups.items()):
            payloads: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for record in deliveries:
                payload = {
                    key: value for key, value in record.items()
                    if key not in ("event_id", "available_at")
                }
                signature = json.dumps(payload, sort_keys=True, default=str)
                payloads[signature].append(record)

            for equivalent in payloads.values():
                if len(equivalent) <= 1:
                    continue
                repeated = True
                exemplar = equivalent[0]
                issues.append({
                    "event_id": event_id,
                    "trade_id": exemplar.get("trade_id"),
                    "account_id": exemplar.get("account_id"),
                    "version": exemplar.get("version"),
                    "reason": "identical_redelivery",
                    "delivery_count": len(equivalent),
                    "duplicate_count": len(equivalent) - 1,
                })
            if len(payloads) > 1:
                uncertain = True
                issues.append({
                    "event_id": event_id,
                    "reason": "conflicting_payload_deferred_to_DQ-03",
                    "distinct_payloads": len(payloads),
                })
        if invalid_count:
            issues.append({
                "reason": "invalid_event_ids_not_evaluated",
                "count": invalid_count,
            })

        result.append(RuleOutcome(
            rule_id="DQ-02",
            status="FAIL" if repeated else ("INDETERMINATE" if uncertain else "PASS"),
            severity="warning",
            issues=issues,
        ))
        return super().handle(cohort, result)
