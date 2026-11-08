"""One trade's source and target histories.

This module provides grouping invariants and a checker hook.
Latest-version selection and comparison rules are the learner's exercise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal, Protocol

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from data_qa.checkers.base import AbstractChecker

from .base import Record
from .trade_result import TradeResult

BusinessKey = tuple[str, int]
Side = Literal["source", "target"]


"""Exception raised when a trade group has no records on either side."""

class EmptyTradeGroupError(ValueError):
    """Raised when a trade group has no records on either side."""


@dataclass(slots=True)
class TradeGroup:
    """All events for ONE business key, kept separately by pipeline side.

    Only structural membership is enforced here. Raw malformed input needs
    validation before grouping; otherwise it can lack a usable business key.
    """

    business_key: BusinessKey
    source: list[Record] = field(default_factory=list)
    target: list[Record] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Copy input lists so subsequent additions do not mutate caller lists.
        source, target = list(self.source), list(self.target)
        self.source, self.target = [], []
        for record in source:
            self.add_source(record)
        for record in target:
            self.add_target(record)

    def _check_membership(self, record: Record) -> None:
        if not isinstance(record, Record):
            raise TypeError("TradeGroup accepts Record instances only")
        if record.business_key() != self.business_key:
            raise ValueError(
                f"Event {record.event_id!r} belongs to {record.business_key()!r}, "
                f"not {self.business_key!r}"
            )

    def add_source(self, record: Record) -> None:
        self._check_membership(record)
        self.source.append(record)

    def add_target(self, record: Record) -> None:
        self._check_membership(record)
        self.target.append(record)

    def latest(self, side: Side) -> Record | None:
        """TODO: select latest unambiguous version on the chosen side.

        Decide what to do if distinct events at the same maximum version
        disagree. Do not silently pick an arbitrary record.
        """
        raise NotImplementedError("Session 05: implement TradeGroup.latest")

    def run_checks(self, checker_chain: AbstractChecker) -> TradeResult:
        """Execute ALL supplied checkers for this group, accumulate issues."""
        if len(self.source) == 0 and len(self.target) == 0:
            raise EmptyTradeGroupError("TradeGroup has no records on either side")

        result = TradeResult(business_key=self.business_key)
        checker_chain.handle(self, result)
        return result
