from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict
from data_qa.data.base import Record


class Handler(ABC):
    """
    Interface for handling requests in a chain of responsibility pattern.
    """

    @abstractmethod
    def set_next(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    def handle(self, source: list[Record], target: list[Record]) -> Dict:
        pass


class AbstractHandler(Handler):
    """
    Default chaining behavior can be implemented inside this base handler class.
    """

    _next_handler: Handler = None

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        # Returning the handler from here will allow us to link handlers in a simple
        # way, like this:
        # _handler.set_next(squirrel).set_next(dog)
        return handler

    @abstractmethod
    def handle(self, source: list[Record], target: list[Record]) -> Dict:
        if self._next_handler:
            return self._next_handler.handle(source, target)

        return None



class MissingHandler(AbstractHandler):
    def handle(self, source: list[Record], target: list[Record]) -> Dict:
        s_business_keys = {record.business_key() for record in source}
        t_business_keys = {record.business_key() for record in target}

        

        result = super().handle(source, target)
        return result


class SquirrelHandler(AbstractHandler):
    def handle(self, source: list[Record], target: list[Record]) -> Dict:
        result = super().handle(source, target)
        return result


class DogHandler(AbstractHandler):
    def handle(self, source: list[Record], target: list[Record]) -> Dict:
        result = super().handle(source, target)
        return result