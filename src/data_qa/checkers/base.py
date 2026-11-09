from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import fields
from decimal import Decimal, InvalidOperation
from data_qa.data.base import Record
from data_qa.data.trade_group import TradeGroup, Side
from data_qa.data.trade_result import TradeResult, IssueCategories


class Checker(ABC):
    """
    Interface for handling requests in a chain of responsibility pattern.
    """

    @abstractmethod
    def set_next(self, handler: Checker) -> Checker:
        pass

    @abstractmethod
    def handle(self, group: TradeGroup, result: TradeResult) -> None:
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
    def handle(self, group: TradeGroup, result: TradeResult) -> None:
        if self._next_handler:
            return self._next_handler.handle(group, result)

        return None


class MissingHandler(AbstractChecker):
    def handle(self, group: TradeGroup, result: TradeResult) -> None:
        if len(group.target) == 0:
            result.add_issue(IssueCategories.MISSING, message="Target is missing")
        return super().handle(group, result)


class ExtraHandler(AbstractChecker):
    def handle(self, group: TradeGroup, result: TradeResult) -> None:
        if len(group.source) == 0:
            result.add_issue(IssueCategories.EXTRA, message="Source is missing")
        return super().handle(group, result)


class DuplicateHandler(AbstractChecker):
    def handle(self, group: TradeGroup, result: TradeResult):
        versions = [src.version for src in group.source] + [
            src.version for src in group.target
        ]
        versions = sorted(set(versions))
        for side in [Side.SOURCE, Side.TARGET]:
            for version in versions:
                records = group.get_side_version(side, version)
                if len(records) <= 1:
                    continue
                if len(records) == 2:
                    for field in fields(records[0]):
                        if getattr(records[0], field.name) != getattr(
                            records[1], field.name
                        ):
                            break
                    else:
                        result.add_issue(
                            IssueCategories.DUPLICATES,
                            side=side,
                            **records[0].__dict__,
                            message="Duplicate records found",
                        )
                else:
                    raise ValueError(
                        f"More than 2 records found for side {side} and version {version}"
                    )
        return super().handle(group, result)


class ChangedHandler(AbstractChecker):
    """Detect conflicting payloads within each side and mismatched final states.

    A repeated identical delivery is handled by DuplicateHandler. Multiple
    distinct payloads at the same version are reported here as a conflict,
    rather than letting latest() select a winner or raise before reporting.
    """

    @staticmethod
    def _pnl_key(value: str | None) -> Decimal | str | None:
        """Compare valid money values exactly; raw invalid values await validation."""
        if value is None:
            return None
        try:
            amount = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return value
        return amount if amount.is_finite() else value

    @classmethod
    def _payload(cls, record: Record) -> tuple[str | None, Decimal | str | None]:
        return record.status, cls._pnl_key(record.pnl)

    def handle(self, group: TradeGroup, result: TradeResult) -> None:
        latest_unambiguous: dict[str, Record] = {}

        # Inspect both sides independently, even if the other side is missing.
        for side in (Side.SOURCE, Side.TARGET):
            records = group.get_side(side)
            if not records:
                continue

            versions = sorted({record.version for record in records})
            for version in versions:
                at_version = group.get_side_version(side, version)
                distinct_payloads = {self._payload(record) for record in at_version}

                if len(distinct_payloads) > 1:
                    event_ids = sorted({record.event_id for record in at_version})
                    evidence = [
                        {"event_id": record.event_id, "status": record.status, "pnl": record.pnl}
                        for record in sorted(
                            at_version,
                            key=lambda record: (
                                record.event_id, str(record.status), str(record.pnl)
                            ),
                        )
                    ]
                    details = {
                        "reason": "payload_conflict",
                        "side": side,
                        "version": version,
                        "event_ids": event_ids,
                        "records": evidence,
                        "message": "Conflicting payloads for the same trade version",
                    }
                    # One immutable event delivered with conflicting contents.
                    if len(event_ids) == 1:
                        details["event_id"] = event_ids[0]
                    result.add_issue(IssueCategories.CHANGED, **details)

                elif version == versions[-1]:
                    # Payload is unambiguous even if identical deliveries repeat.
                    latest_unambiguous[side] = min(
                        at_version,
                        key=lambda record: (
                            record.event_id, str(record.status), str(record.pnl)
                        ),
                    )

        source_latest = latest_unambiguous.get(Side.SOURCE)
        target_latest = latest_unambiguous.get(Side.TARGET)

        if source_latest is not None and target_latest is not None:
            if source_latest.version == target_latest.version:
                if self._pnl_key(source_latest.pnl) != self._pnl_key(target_latest.pnl):
                    result.add_issue(
                        IssueCategories.CHANGED,
                        reason="state_mismatch",
                        field="pnl",
                        version=source_latest.version,
                        source_value=source_latest.pnl,
                        target_value=target_latest.pnl,
                        message="PNL differs between source and target",
                    )

                if source_latest.status != target_latest.status:
                    result.add_issue(
                        IssueCategories.CHANGED,
                        reason="state_mismatch",
                        field="status",
                        version=source_latest.version,
                        source_value=source_latest.status,
                        target_value=target_latest.status,
                        message="Status differs between source and target",
                    )
            # Different latest versions are intentionally a separate rule.

        return super().handle(group, result)


data_checkers = MissingHandler()
data_checkers.set_next(ExtraHandler()).set_next(DuplicateHandler()).set_next(ChangedHandler())
