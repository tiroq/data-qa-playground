from __future__ import annotations
from abc import ABC, abstractmethod
from data_qa.data.base import TradeGroup, TradeResult
from data_qa.data.trade_result import IssueCategory


class Handler(ABC):
    """
    Interface for handling requests in a chain of responsibility pattern.
    """

    @abstractmethod
    def set_next(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    def handle(self, trade_group: TradeGroup) -> TradeResult:
        pass


class AbstractHandler(Handler):
    """
    Default chaining behavior can be implemented inside this base handler class.
    """

    def __init__(self) -> None:
        self._next_handler = None
        self.result = TradeResult()

    # _next_handler: Handler = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        # Returning the handler from here will allow us to link handlers in a simple
        # way, like this:
        # _handler.set_next(squirrel).set_next(dog)
        return handler

    @abstractmethod
    def handle(self, trade_group: TradeGroup) -> None:
        if self._next_handler:
            return self._next_handler.handle(trade_group)

        return None



class MissingHandler(AbstractHandler):
    def handle(self, trade_group: TradeGroup) -> None:
        if len(trade_group.target) == 0:
            self.result.add_issue(IssueCategory.MISSING, {"message": "Target is missing"})
        return super().handle(trade_group)


class SquirrelHandler(AbstractHandler):
    def handle(self, trade_group: TradeGroup) -> None:
        result = super().handle(trade_group)
        return result


class DogHandler(AbstractHandler):
    def handle(self, trade_group: TradeGroup) -> None:
        result = super().handle(trade_group)
        return result