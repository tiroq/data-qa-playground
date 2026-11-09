from __future__ import annotations
from abc import ABC, abstractmethod
from collections import Counter
from decimal import Decimal
from data_qa.data.base import Record, pnl_value
from data_qa.data.trade_group import AmbiguousLatestVersionError, TradeGroup, Side
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
        if len(group.target) == 0 and not group.context.target.possibly_excluded:
            result.add_issue(IssueCategories.MISSING, message="Target is missing")
        return super().handle(group, result)


class ExtraHandler(AbstractChecker):
    def handle(self, group: TradeGroup, result: TradeResult) -> None:
        if len(group.source) == 0 and not group.context.source.possibly_excluded:
            result.add_issue(IssueCategories.EXTRA, message="Source is missing")
        return super().handle(group, result)


class DuplicateHandler(AbstractChecker):
    def handle(self, group: TradeGroup, result: TradeResult) -> None:
        for side in (Side.SOURCE, Side.TARGET):
            counts = Counter(
                (r.event_id, r.version, r.status, pnl_value(r.pnl))
                for r in group.get_side(side)
            )

            for (event_id, version, status, pnl), count in sorted(
                counts.items(),
                key=lambda item: (
                    str(item[0][0]),
                    item[0][1],
                    str(item[0][2]),
                    str(item[0][3]),
                ),
            ):
                if count <= 1:
                    continue

                result.add_issue(
                    IssueCategories.DUPLICATES,
                    side=side,
                    event_id=event_id,
                    version=version,
                    delivery_count=count,
                    duplicate_count=count - 1,
                    message="Duplicate deliveries found",
                )

        return super().handle(group, result)


class ChangedHandler(AbstractChecker):
    """Detect conflicting payloads within each side and mismatched final states.

    A repeated identical delivery is handled by DuplicateHandler. Multiple
    distinct payloads at the same version are reported here as a conflict,
    rather than letting latest() select a winner or raise before reporting.
    """

    _pnl_key = staticmethod(pnl_value)

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

        if (
            source_latest is not None
            and target_latest is not None
            and not group.context.source.latest_uncertain
            and not group.context.target.latest_uncertain
        ):
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



class VersionMismatchHandler(AbstractChecker):
    """Report latest-version divergence independently from payload comparison."""

    def handle(self, group: TradeGroup, result: TradeResult) -> None:
        if (
            not group.source
            or not group.target
            or group.context.source.latest_uncertain
            or group.context.target.latest_uncertain
        ):
            return super().handle(group, result)

        try:
            source_latest = group.latest(Side.SOURCE)
            target_latest = group.latest(Side.TARGET)
        except AmbiguousLatestVersionError:
            # ChangedHandler reports contradictory same-version payloads.
            # We must not choose a winner just to compare version numbers.
            return super().handle(group, result)

        if source_latest is None or target_latest is None:
            return super().handle(group, result)

        if source_latest.version != target_latest.version:
            result.add_issue(
                IssueCategories.CHANGED,
                reason="version_mismatch",
                source_version=source_latest.version,
                target_version=target_latest.version,
                direction=(
                    "target_behind"
                    if source_latest.version > target_latest.version
                    else "target_ahead"
                ),
                message="Latest source and target versions do not match",
            )

        return super().handle(group, result)


data_checkers = MissingHandler()
data_checkers.set_next(ExtraHandler()).set_next(DuplicateHandler()).set_next(
    ChangedHandler()
).set_next(VersionMismatchHandler())
