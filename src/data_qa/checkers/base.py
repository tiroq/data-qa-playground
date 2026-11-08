from __future__ import annotations
from abc import ABC, abstractmethod
from data_qa.data.trade_group import TradeGroup
from data_qa.data.trade_result import TradeResult, IssueCategories


class Checker(ABC):
    """
    Interface for handling requests in a chain of responsibility pattern.
    """

    @abstractmethod
    def set_next(self, handler: Checker) -> Checker:
        pass

    @abstractmethod
    def handle(self, group: TradeGroup) -> TradeResult:
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


data_checkers = MissingHandler()
data_checkers.set_next(ExtraHandler())