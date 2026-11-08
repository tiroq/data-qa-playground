"""Test infrastructure for Session 07 — NOT a database or network integration.

The fake preserves physical submissions and is intentionally not idempotent.
No pytest fixtures or assertions are provided here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakePipeline:
    fail_processing: bool = False
    source: list[dict[str, Any]] = field(default_factory=list)
    target: list[dict[str, Any]] = field(default_factory=list)
    _pending: list[dict[str, Any]] = field(default_factory=list)

    def submit(self, event: dict[str, Any]) -> str:
        if not event.get("event_id"):
            raise ValueError("event_id is required")
        record = deepcopy(event)
        self.source.append(record)
        self._pending.append(deepcopy(record))
        return str(record["event_id"])

    def drain(self) -> int:
        """Process pending events; no writes if failure injection is active."""
        if self.fail_processing:
            raise RuntimeError("synthetic processing failure")
        count = len(self._pending)
        self.target.extend(self._pending)
        self._pending.clear()
        return count

    def reset(self) -> None:
        self.source.clear()
        self.target.clear()
        self._pending.clear()


if __name__ == "__main__":
    pipeline = FakePipeline()
    pipeline.submit({"event_id": "demo", "trade_id": "T1", "account_id": "A1"})
    print(f"queued={len(pipeline.source)} target_before={len(pipeline.target)}")
    pipeline.drain()
    print(f"target_after={len(pipeline.target)}")
