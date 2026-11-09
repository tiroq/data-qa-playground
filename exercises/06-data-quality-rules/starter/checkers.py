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
