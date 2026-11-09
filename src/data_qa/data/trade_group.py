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

from .base import Record, pnl_value
from .check_context import CheckContext
from .trade_result import TradeResult

BusinessKey = tuple[str, int]


class Side(str):
    SOURCE = "source"
    TARGET = "target"

Sides = Literal["source", "target"]


"""Exception raised when a trade group has no records on either side."""

class EmptyTradeGroupError(ValueError):
    """Raised when a trade group has no records on either side."""

class AmbiguousLatestVersionError(ValueError):
    """Raised when multiple records share the latest version on a side."""


@dataclass(slots=True)
class TradeGroup:
    """All events for ONE business key, kept separately by pipeline side.

    Only structural membership is enforced here. Raw malformed input needs
    validation before grouping; otherwise it can lack a usable business key.
    """

    business_key: BusinessKey
    source: list[Record] = field(default_factory=list)
    target: list[Record] = field(default_factory=list)
    context: CheckContext = field(default_factory=CheckContext, repr=False)

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

    def latest(self, side: Sides) -> Record | None:
        """Select latest unambiguous version on the chosen side.

        Decide what to do if distinct events at the same maximum version
        disagree. Do not silently pick an arbitrary record.
        """
        records = self.source if side == Side.SOURCE else self.target
        if not records or len(records) == 0:
            return None
        max_version = max(record.version for record in records)
        latest_records = [record for record in records if record.version == max_version]
        payloads = {
            (record.status, pnl_value(record.pnl))
            for record in latest_records
        }

        if len(payloads) == 1:
            return min(latest_records, key=lambda record: record.event_id)
        # Ambiguous: multiple records with the same max version
        raise AmbiguousLatestVersionError(f"Ambiguous latest version conflict for side {side}")

    def run_checks(self, checker_chain: AbstractChecker) -> TradeResult:
        """Execute ALL supplied checkers for this group, accumulate issues."""
        if len(self.source) == 0 and len(self.target) == 0:
            raise EmptyTradeGroupError(
                f"TradeGroup {self.business_key!r} has no records on either side"
            )

        result = TradeResult(business_key=self.business_key)
        checker_chain.handle(self, result)
        return result

    def get_side(self, side: Sides | None = None) -> list[Record]:
        if side is None:
            return [*self.source, *self.target]
        if side == Side.SOURCE:
            return list(self.source)
        if side == Side.TARGET:
            return list(self.target)
        raise ValueError(f"Unknown side {side!r}")

    def get_side_version(self, side: Sides, version: int) -> list[Record]:
        records = self.get_side(side=side)
        return [r for r in records if r.version == version]
