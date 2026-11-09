from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import fields
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
    def handle(self, group: TradeGroup, result: TradeResult) -> None:
        if len(group.source) == 0 or len(group.target) == 0:
            return super().handle(group, result)

        source_latest = group.latest(Side.SOURCE)
        target_latest = group.latest(Side.TARGET)

        if source_latest.version != target_latest.version:
            # Not responsible for version mismatches
            return super().handle(group, result)

        if source_latest.pnl != target_latest.pnl:
            result.add_issue(
                IssueCategories.CHANGED,
                source=source_latest,
                target=target_latest,
                message="PNL has changed between source and target",
            )

        if source_latest.status != target_latest.status:
            result.add_issue(
                IssueCategories.CHANGED,
                source=source_latest,
                target=target_latest,
                message="Status has changed between source and target",
            )

        return super().handle(group, result)


data_checkers = MissingHandler()
data_checkers.set_next(ExtraHandler()).set_next(DuplicateHandler()).set_next(ChangedHandler())
