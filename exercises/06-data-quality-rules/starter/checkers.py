from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from rule_runner import RuleOutcome


class Checker(ABC):
    """
    Interface for handling requests in a chain of responsibility pattern.
    """

    @abstractmethod
    def set_next(self, handler: Checker) -> Checker:
        pass

    @abstractmethod
    def handle(self, cohort: dict[str, Any]) -> None:
        pass


class AbstractChecker(Checker):
    """
    Default chaining behavior can be implemented inside this base handler class.
    """

    _next_handler: Checker = None

    def set_next(self, handler: Checker) -> Checker:
        self._next_handler = handler
        # Returning the handler from here will allow us to link handlers in a simple
        # way, like this:
        # _handler.set_next(squirrel).set_next(dog)
        return handler

    @abstractmethod
    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        if self._next_handler:
            return self._next_handler.handle(cohort, result)

        return None


class FieldsChecker(AbstractChecker):
    def handle(self, cohort: dict[str, Any], result: list[RuleOutcome]) -> None:
        outcome = RuleOutcome(
            rule_id="missing_field",
            status="PASS",
            severity="critical",
            issues=[],
        )
        for record in cohort["records"]:
            for field in ["event_id", "trade_id", "account_id", "version", "status"]:
                if record.get(field, None) is None:
                    outcome.status = "FAIL"
                    outcome.issues.append(
                        {
                            "event_id": record.get("event_id"),
                            "field": field,
                            "reason": "required_field_is_null",
                            "message": f"Required field '{field}' is null",
                        })
        result.append(outcome)
        return super().handle(cohort, result)